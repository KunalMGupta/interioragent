"""
Phase-1 verification scene (underscore-prefixed so batchgen ignores it).

All objects are DIRECT floor children of the room and axis-aligned, so the three
constraint mechanisms can be read cleanly:

  1. AUTO door clearance — `sofa` is placed against the front wall, exactly where a
     centred front-wall door is. With zero author action it must end up pushed clear
     of the doorway (z well away from the front wall at z=DEPTH).
  2. MANUAL clearance — `cabinet` on the back wall gets add_clearance(dir="front"); the
     `stool` placed in front of it must be pushed out of that 0.8 m band.
  3. MANUAL visibility — add_visibility(sofa, cabinet) runs along +z (axis-aligned); the
     `stool` sitting on that sightline must be pushed laterally out of the way.

Diagnostics print after compile so we can assert the doorway is actually clear.
"""
import numpy as np
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("DoorClearanceTest", seed=7)

with scene.RoomGroup(modulate_scale=1.0, randomness=0.0) as room:
    room.place_walls(floor_texture="light oak planks",
                     ceiling_texture="warm white", wall_texture="warm beige")
    sofa = scene.AddAsset("a grey 3-seat sofa")
    room.place_on_front(sofa, facing="back")          # at the front wall == the doorway
    cabinet = scene.AddAsset("a tall wooden storage cabinet")
    room.place_on_back_wall_center(cabinet)
    stool = scene.AddAsset("a small round wooden stool")
    room.place_on_back(stool)                          # in front of the cabinet / on sightline
    room.add_clearance(cabinet, distance=0.8, dir="front")
    room.add_visibility(sofa, cabinet)
    room.place_door("front_wall", position="center")

scene.export("_door_clearance_test.blend")

# ---- diagnostics -----------------------------------------------------------
def loc(o):
    l = o.get_location()
    return float(l[0]), float(l[2])

print("\n===== DOOR-CLEARANCE DIAGNOSTICS =====")
print(f"room WIDTH={room.WIDTH:.2f} DEPTH={room.DEPTH:.2f}")
proxies = [c for c in room.children if getattr(c, "is_proxy", False)]
for p in proxies:
    px, pz = loc(p)
    print(f"door proxy: loc=(x={px:.2f}, z={pz:.2f}) rot={p.get_rotation():.0f} "
          f"(front wall at z={room.DEPTH:.2f})")
for label, o in [("sofa", sofa), ("cabinet", cabinet), ("stool", stool)]:
    x, z = loc(o)
    print(f"{label:8s} loc=(x={x:.2f}, z={z:.2f})")

sofa_zmax = float(sofa.get_aabb()[1, 2])
band_inner = room.DEPTH - room.DOOR_CLEARANCE
print(f"[door]  sofa front-face z={sofa_zmax:.2f}, doorway band inner edge z={band_inner:.2f} "
      f"-> {'PASS' if sofa_zmax <= band_inner + 0.05 else 'FAIL'} (face must clear the band)")
# cabinet faces +z (front); stool should be pushed >0.8 in z OR off-axis in x
cx, cz = loc(cabinet)
stx, stz = loc(stool)
print(f"[clear] stool front-gap from cabinet (z): {stz - cz:.2f} m")
print(f"[vis]   stool lateral offset from sofa-x: {abs(stx - loc(sofa)[0]):.2f} m")
print("======================================\n")
