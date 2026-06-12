import ezdxf

doc = ezdxf.readfile("my_building.dxf") #the file we made in script_b.py
msp = doc.modelspace()

# we need to find all circles on the columns layer and move the first one
for entity in msp.query('CIRCLE[layer=="Columns"]'):
    old_center = entity.dxf.center
    print(f"Moving column from {old_center}")

    # Moving it two units to the right
    entity.dxf.center = (old_center.x + 2, old_center.y, old_center.z)
    print(f"New Position: {entity.dxf.center}")
    break # We only want to move the first one

doc.saveas("my_building_modified.dxf")
print("DXF file modified successfully!")