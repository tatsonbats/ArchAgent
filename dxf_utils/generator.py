# dxf_utils/generator.py
#
# This file does two things:
#   1. Uses an LLM to extract building parameters from a natural language brief
#   2. Uses those parameters to generate a valid DXF file from scratch
#
# It is called by the Generator Agent during the hackathon pipeline,
# but you can also run it standalone to test it.

import os           # lets us read environment variables (like API keys)
import json         # lets us parse JSON text into Python dicts
import ezdxf        # the library that creates and edits DXF files
from anthropic import Anthropic   # the library that lets us call Claude
from dotenv import load_dotenv    # reads our .env file so we don't hardcode API keys

# Load the .env file so os.getenv() can find our API key
load_dotenv()

# Create a single Anthropic client that both functions will share
# It automatically picks up ANTHROPIC_API_KEY from your .env file
client = Anthropic()


# ─────────────────────────────────────────────────────────────
# FUNCTION 1: Extract parameters from a natural language brief
# ─────────────────────────────────────────────────────────────

def extract_params_from_brief(brief: str) -> dict:
    """
    Takes a natural language brief like:
      "office building, 3 floors, 500m2 footprint, steel frame, flat roof"

    And returns a Python dict like:
      {
        "floors": 3,
        "footprint_x": 25.0,
        "footprint_y": 20.0,
        "grid_spacing": 5.0,
        "frame_type": "steel",
        "project_name": "Office Building"
      }

    The LLM does the reading comprehension. We just parse its output.
    """

    # This is the instruction we give the LLM.
    # We are very specific: output ONLY JSON, no extra text.
    # We tell it exactly what fields we want and what to do if something is missing.
    prompt = f"""
You are a building parameter extraction assistant.

Read the following architectural brief and extract the key building parameters.
Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

Brief: "{brief}"

Return exactly this JSON structure:
{{
  "project_name": "short descriptive name derived from the brief",
  "floors": <integer, number of floors, default 3 if not mentioned>,
  "footprint_x": <float, building width in metres. If total area given, assume square root. Default 20.0>,
  "footprint_y": <float, building depth in metres. If total area given, assume square root. Default 15.0>,
  "grid_spacing": <float, column grid spacing in metres. Default 5.0 for steel, 6.0 for concrete>,
  "frame_type": "<'steel' or 'concrete', default 'steel' if not mentioned>"
}}

Only return the JSON object. Nothing else.
"""

    # Call the LLM with our prompt
    response = client.messages.create(
        model="claude-sonnet-4-20250514",  # the model we're using
        max_tokens=300,                    # keep it short — we only need a small JSON
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # The LLM's response is inside response.content[0].text
    # It should be a JSON string like: {"floors": 3, "footprint_x": 25.0, ...}
    raw_text = response.content[0].text.strip()

    # Sometimes LLMs wrap their output in ```json ... ``` even when told not to.
    # These two lines strip that out just in case.
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    # Convert the JSON string into an actual Python dict
    params = json.loads(raw_text)

    # Print what we got so we can see it during testing
    print(f"[Generator] Extracted parameters: {json.dumps(params, indent=2)}")

    return params


# ─────────────────────────────────────────────────────────────
# FUNCTION 2: Generate a DXF file from a parameters dict
# ─────────────────────────────────────────────────────────────

def generate_building_dxf(params: dict, output_path: str = "demo_files/generated.dxf") -> str:
    """
    Takes a parameters dict (either from extract_params_from_brief or typed manually)
    and draws a building floor plan as a DXF file.

    Returns the file path of the saved DXF.

    The DXF contains:
    - A rectangular perimeter wall (the building outline)
    - Columns at regular grid intervals inside that outline
    - Text labels for NORTH, floor count, and frame type
    """

    # ── Step 1: Validate inputs ──────────────────────────────
    # These checks prevent the function from crashing with a confusing error later.
    # Better to fail early with a clear message.

    floors = int(params.get("floors", 3))
    fx = float(params.get("footprint_x", 20.0))   # building width
    fy = float(params.get("footprint_y", 15.0))   # building depth
    gs = float(params.get("grid_spacing", 5.0))   # column grid spacing
    frame = str(params.get("frame_type", "steel")).upper()
    name = str(params.get("project_name", "Building"))

    if fx <= 0 or fy <= 0:
        raise ValueError(f"Footprint dimensions must be positive. Got: {fx} x {fy}")
    if floors < 1:
        raise ValueError(f"Building must have at least 1 floor. Got: {floors}")
    if gs <= 0:
        raise ValueError(f"Grid spacing must be positive. Got: {gs}")


    # ── Step 2: Create a new empty DXF document ──────────────
    # ezdxf.new() creates a blank DXF in memory — nothing on disk yet.
    # "R2010" is the DXF format version. R2010 works with all modern AutoCAD versions.
    doc = ezdxf.new("R2010")

    # modelspace() is the main drawing area in AutoCAD.
    # Think of it as the blank canvas where we'll draw things.
    msp = doc.modelspace()


    # ── Step 3: Create layers ────────────────────────────────
    # In AutoCAD, layers are like transparent overlays — walls go on one,
    # columns on another, text on another. This lets architects toggle them
    # on and off independently. The color numbers are AutoCAD's color index:
    #   1 = red, 2 = yellow, 3 = green, 4 = cyan, 5 = blue, 7 = white/black

    doc.layers.add("WALL-EXT",    color=1)   # red  — exterior walls
    doc.layers.add("COLUMN-STR",  color=3)   # green — structural columns
    doc.layers.add("ANNOTATIONS", color=7)   # white/black — text labels


    # ── Step 4: Draw the perimeter walls ────────────────────
    # add_lwpolyline draws a connected series of line segments.
    # We give it 4 corner points to make a rectangle.
    # close=True means it automatically draws the last segment back to the first point,
    # completing the rectangle. Without it, we'd have a 3-sided shape.
    #
    # The coordinates are: bottom-left, bottom-right, top-right, top-left
    # (0,0) is the bottom-left corner of the building.

    msp.add_lwpolyline(
        [(0, 0), (fx, 0), (fx, fy), (0, fy)],  # four corners
        close=True,                              # connect last point back to first
        dxfattribs={"layer": "WALL-EXT"}        # put it on the WALL-EXT layer
    )


    # ── Step 5: Draw columns at grid intersections ───────────
    # We want columns placed at regular intervals across the building footprint.
    # For example: if the building is 25m wide and the grid is 5m,
    # we place columns at x = 0, 5, 10, 15, 20, 25.
    # Same logic for y.
    #
    # The nested while loops walk across the grid:
    #   Outer loop: move along x axis in steps of grid_spacing
    #   Inner loop: for each x position, move along y axis in steps of grid_spacing
    #
    # Each column is drawn as a small circle (radius 0.3m = 300mm, a realistic column size).

    x = 0.0
    while x <= fx + 0.01:   # +0.01 handles floating point rounding (e.g. 25.0000001 > 25.0)
        y = 0.0
        while y <= fy + 0.01:
            msp.add_circle(
                center=(x, y, 0),              # centre point of the circle (x, y, z=0 for 2D)
                radius=0.3,                    # 300mm column radius
                dxfattribs={"layer": "COLUMN-STR"}
            )
            y += gs   # move to next row
        x += gs       # move to next column


    # ── Step 6: Add text annotations ────────────────────────
    # We add three text labels to the drawing:
    #   1. "NORTH" — tells the Geometry Agent (and humans) which direction is north
    #   2. "FLOORS: 3" — records the floor count in the drawing itself
    #   3. "FRAME: STEEL" — records the frame type
    #
    # set_placement((x, y)) positions the text in the drawing.
    # height= is the text size in the same units as the drawing (metres here).

    # NORTH label sits above the building (at y = footprint_y + 2 metres)
    msp.add_text(
        "NORTH",
        dxfattribs={"layer": "ANNOTATIONS", "height": 1.5}
    ).set_placement((fx / 2, fy + 2))   # centred horizontally above the building

    # Floor count sits below the building
    msp.add_text(
        f"FLOORS: {floors}",
        dxfattribs={"layer": "ANNOTATIONS", "height": 0.8}
    ).set_placement((0, -2))

    # Frame type sits below the floor count
    msp.add_text(
        f"FRAME: {frame}",
        dxfattribs={"layer": "ANNOTATIONS", "height": 0.8}
    ).set_placement((0, -3.5))

    # Project name sits below that
    msp.add_text(
        name.upper(),
        dxfattribs={"layer": "ANNOTATIONS", "height": 1.0}
    ).set_placement((0, -5.5))


    # ── Step 7: Make sure the output folder exists ───────────
    # If demo_files/ doesn't exist yet, os.makedirs creates it.
    # exist_ok=True means it won't crash if the folder already exists.
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)


    # ── Step 8: Save the DXF file to disk ───────────────────
    # Nothing has touched the disk until this line.
    # Everything before was building the DXF in memory.
    doc.saveas(output_path)

    print(f"[Generator] DXF saved to: {output_path}")

    # Return the path so the calling code knows where the file is
    return output_path


# ─────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTION: Do both steps at once
# ─────────────────────────────────────────────────────────────

def generate_from_brief(brief: str, output_path: str = "demo_files/generated.dxf") -> str:
    """
    Combines both functions above into one call.
    Takes a natural language brief, returns a DXF file path.

    This is what the Generator Agent will call during the hackathon.
    """
    params = extract_params_from_brief(brief)
    return generate_building_dxf(params, output_path)