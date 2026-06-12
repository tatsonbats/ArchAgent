# tests/test_generator.py
#
# Run this file to verify your generator works before the competition.
# Run it with: python tests/test_generator.py
#
# What it tests:
#   1. Generating from a manually written parameters dict (no LLM needed)
#   2. Generating from a natural language brief (uses LLM)
#   3. Edge cases — what happens with weird inputs

import sys
import os

# This line adds the parent folder (arch-agents/) to Python's search path.
# Without it, Python can't find the dxf_utils package when you run this
# from inside the tests/ subfolder.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dxf_utils.generator import generate_building_dxf, extract_params_from_brief, generate_from_brief


# ── Test 1: Small building from manual params ─────────────────
# This test does NOT call the LLM — it just tests the DXF drawing function.
# Use this first, before testing the LLM part.

print("\n── Test 1: Small building (manual params) ──")
small_params = {
    "project_name": "Small House",
    "floors": 2,
    "footprint_x": 10.0,
    "footprint_y": 8.0,
    "grid_spacing": 4.0,
    "frame_type": "steel"
}
path = generate_building_dxf(small_params, output_path="demo_files/test_small.dxf")
print(f"✓ File created at: {path}")
# To verify: open demo_files/test_small.dxf in LibreCAD or sharecad.org
# You should see: a 10×8 rectangle, columns at (0,0) (4,0) (8,0) (10,0)
#                 and matching rows at y=4 and y=8. Text above says NORTH.


# ── Test 2: Medium building from manual params ────────────────
print("\n── Test 2: Medium office building (manual params) ──")
medium_params = {
    "project_name": "Office Block",
    "floors": 3,
    "footprint_x": 25.0,
    "footprint_y": 20.0,
    "grid_spacing": 5.0,
    "frame_type": "steel"
}
path = generate_building_dxf(medium_params, output_path="demo_files/test_medium.dxf")
print(f"✓ File created at: {path}")


# ── Test 3: Large building from manual params ─────────────────
print("\n── Test 3: Large warehouse (manual params) ──")
large_params = {
    "project_name": "Warehouse",
    "floors": 1,
    "footprint_x": 60.0,
    "footprint_y": 40.0,
    "grid_spacing": 8.0,
    "frame_type": "steel"
}
path = generate_building_dxf(large_params, output_path="demo_files/test_large.dxf")
print(f"✓ File created at: {path}")


# ── Test 4: LLM parameter extraction (requires API key) ───────
# This test calls the LLM. Make sure your .env file has ANTHROPIC_API_KEY set.
print("\n── Test 4: LLM parameter extraction from brief ──")
brief = "A residential apartment building with 5 floors, 400 square metre footprint, concrete frame"
params = extract_params_from_brief(brief)
print(f"✓ LLM extracted: {params}")
# Check: do the numbers make sense for the brief you gave it?
# floors should be 5, frame_type should be "concrete"


# ── Test 5: Full pipeline from brief to DXF ───────────────────
print("\n── Test 5: End-to-end brief → DXF ──")
path = generate_from_brief(
    "hospital, 4 floors, 800m2 footprint, steel frame",
    output_path="demo_files/test_from_brief.dxf"
)
print(f"✓ Full pipeline complete. File at: {path}")


# ── Test 6: Edge case — bad inputs ────────────────────────────
print("\n── Test 6: Edge case — negative footprint ──")
try:
    bad_params = {"floors": 3, "footprint_x": -10.0, "footprint_y": 20.0, "grid_spacing": 5.0}
    generate_building_dxf(bad_params, output_path="demo_files/test_bad.dxf")
    print("✗ Should have raised an error but didn't")
except ValueError as e:
    print(f"✓ Correctly raised ValueError: {e}")


print("\n── All tests complete ──")
print("Open the files in demo_files/ using LibreCAD (free) or https://sharecad.org")