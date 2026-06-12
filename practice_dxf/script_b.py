import ezdxf

doc = ezdxf.new()
msp = doc.modelspace()

# We need to create a layer for walls and a layer for collumns
doc.layers.add("Walls", color=1)  # Red; 1= red in autoCAD
doc.layers.add("Columns", color=2)  # Yellow; 2= yellow in autoCAD

# We now need to make 4 walls as a rectangle 
# These are 4 coordinates for the walls. format is (x,y) pairs going around the building
msp.add_lwpolyline(
    [(0, 0), (20, 0), (20, 15), (0, 15)],
    close=True, 
    dxfattribs={'layer': 'Walls'}
)

# Now we need to add 4 collumns at the corners of the building. We can use circles for this
for x, y in [(0, 0), (20, 0), (20, 15), (0, 15)]:
    msp.add_circle(
        center=(x, y), 
        radius=0.3, 
        dxfattribs={'layer': 'Columns'}
        )

# add a text label for the building
msp.add_text(
    "NORTH",
    dxfattribs={"layer": "ANNOTATIONS", "height": 1.0}
).set_placement((10, 16))

doc.saveas("my_building.dxf")
print("DXF file created successfully!")