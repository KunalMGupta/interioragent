"""
Hair salon — "Luxe Row-Station Salon Spine" (planner target tmp/salon_plan/plan.png).
Blush + brass + concrete. Approach A: dressing-table styling stations (mirror+counter+
drawers) with a barber chair in FRONT facing the mirror — per-station mirrors sidestep the
3-slots-per-wall limit. Backwash units on the 3 right-wall slots. Reception + waiting at entry.

PHASE 1 — floor anchors (layout + proportions). Plants/rug/retail/neon/window come later.
"""
from IDSDL.scene import SceneProgRoom

scene = SceneProgRoom("HairSalonPretty", seed=77)

# --- one styling station: dressing-table console + barber chair (client faces the mirror) ---
with scene.RelativeGroup() as station:
    console = scene.AddAsset("a salon styling station with a mirror and drawers")
    station.place_desk_chair(console, scene.AddAsset("a salon styling chair"), gap=True)
    station.add_lighting("a brass pendant light", density=0)     # per-station light (×5)

# --- 5 stations rowed along the back (mirror) wall ---
with scene.GridGroup(sparsity=0.5) as spine:
    spine.place_row(5 * station)

# --- backwash shampoo units: one per right-wall slot (floor-adjacent, basins to the wall) ---
backwash = 3 * scene.AddAsset("a salon backwash shampoo unit")

# --- curved reception desk at the entry ---
with scene.RelativeGroup() as reception:
    reception.set_anchor(scene.AddAsset("a curved salon reception desk"))
    reception.add_lighting("a brass pendant light", density=0)

# --- cozy waiting nook ---
with scene.RelativeGroup() as waiting:
    sofa = scene.AddAsset("a dusty pink velvet two-seat sofa")
    waiting.set_anchor(sofa)
    waiting.place_on_front_right(scene.AddAsset("a gold magazine rack"))

with scene.RoomGroup(modulate_scale=0.85, randomness=0.1) as room:
    room.place_walls(floor_texture="polished concrete floor",
                     ceiling_texture="white", wall_texture="soft blush pink")
    room.place_on_back(spine, facing="back")
    room.face(spine, toward="front_wall")          # tables to back wall, chairs to room (clients face mirror)
    room.place_on_right_wall_left(backwash[0])
    room.place_on_right_wall_center(backwash[1])
    room.place_on_right_wall_right(backwash[2])
    room.place_on_front_right(reception)
    room.place_on_front_left_corner(waiting)
    room.place_door("front_wall", position="center")

scene.export("salon_pretty.blend")
