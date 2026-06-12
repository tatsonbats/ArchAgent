import ezdxf

doc = ezdxf.readfile(r"C:\Users\btatv\ArchAgent\practice_dxf\American Farmhouse 2021-03-01.dxf")
msp = doc.modelspace()

for entity in msp:
    print(f"Type: {entity.dxftype()}, Layer: {entity.dxf.layer}")