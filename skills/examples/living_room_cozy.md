# Cozy living room — worked example

Scene: `scenes/work/living_room_cozy.py` (seed=42), planner-driven **"Cozy Hearth-Centric Living
Room"**, built via the guided 9-gate flow. The core **residential lounge** pattern: a **hearth focal
wall** the seating hero faces, a **conversation cluster** (sectional + coffee table + angled leather
nook) on a defined rug, a **filled bookcase** as balancing visual mass. Converged fully clean
(`no rescale` / `no rotation` / `no wall overlap`, no lints) in four builds (2× phase-1, 1× phase-2
retry, 2× full).

## Prompt this covers
- "a (cozy) living room / lounge / family room / den": sofa facing a fireplace or media wall across
  a coffee table on a rug, accent chair(s), bookcase, lamps, window, wall art.

## Layout pattern — hearth focal wall + facing conversation cluster
- **Fireplace** = `place_on_back_wall_center` (floor asset against the wall; its 0.8 m functional
  front clearance comes FREE from `CategoryClearanceConstraint`). Framed photo gallery hung ABOVE it
  with `place_on_wall_back_center` — wall-mounted art and wall-adjacent floor furniture occupy
  independent slots, so this stacks cleanly.
- **Seating hero** = a `RelativeGroup` anchored on the sectional, placed
  `room.place_on_center(seating, facing="back")` so the sofa looks at the fire: coffee table on the
  front (between sofa and hearth), the leather nook on `place_on_front_right_further` +
  `seating.face(nook, toward=coffee)` (side placements bake ±90° — always face flanking seats at the
  cluster anchor), `place_rug` under everything, `add_lighting(flush, density=0)` = ONE central
  fixture.
- **Leather nook** is its own `RelativeGroup` (chair anchor + ottoman `place_on_front_adjacent` +
  side table left + brass floor lamp back; table lamp on top of the side table in phase 2) — the
  seat travels with its table and its light as one unit, and `face()` works on the nested group.
- **Bookcase** (pinned pre-FILLED mesh) on the left wall; scaled to a target HEIGHT uniformly via
  `obj.scale(obj.get_width() * H / obj.get_height())`.
- **Window** standard (not floor-to-ceiling — black-void lesson) on the right wall with **plum
  curtains** — the plan's accent color delivered through a textile, since unpinned textiles are
  where palette accents are cheap and safe.

## Lessons this scene encodes

### 1. A "corner" mesh betrays itself only in the room render — eyeball placements, not just previews
The audit-gate fireplace pick (`hssd/9a81f950…`, strongest fire glow) was captioned "white **corner**
fireplace"; straight-on its preview looked normal. Placed at the back wall CENTER, the phase-1 render
showed V-angled wings. → Swapped to the straight wood-mantel unit (`hssd/afbe5bf0…`). The cheap
phase-1 loop exists exactly for this: a mesh's *form factor* (corner vs straight) is a layout
property you only verify in situ.

### 2. `place_rug` size is relative to the GROUP bbox — a full cluster at 1.0 reads as carpet
`size=1.0` under a seating group whose bbox spans sofa + nook + coffee table covered nearly the whole
auto-sized floor → read as wall-to-wall carpet, not "a rug defining the seating zone". `size=0.75`
let the dark walnut floor frame it. Rule of thumb: for a room-dominating cluster, rug size ≤ 0.8.

### 3. A room-size vote that NEVER flips is signal, not drift
Every prior scene's `RoomProportions` drift eventually flipped direction (enlarge→shrink) — the basis
of "hold early, act last". Here the vote was **enlarge in every phase** (1.2 → 1.25 → 1.1 → 1.1),
monotonically decaying but never flipping. Applied the final-phase `modulate_scale=1.1` → immediate
`no rescale`. Refinement: *hold early* still, but read persistence+direction — a unidirectional vote
train converges in one application; a flip-flopping one means the early votes were premature.

### 4. Ottoman scale: shrink uniformly, judge against its chair
The pinned cognac footstool came in near chair-sized (scale metadata 1.2). `modulate_scale=0.7`
(uniform — never `width=` on a bad-scale asset, the children_room squash lesson) sat it correctly at
the chair's feet.

### 5. Declined VLM noise (weak-smoke-alarm rule holds)
Phase-1 emitted `rotate left/right accent chair to face the coffee table` — the scene has ONE accent
chair, and `face(nook, toward=coffee)` had already angled it (confirmed in the render). Declined;
the vote never returned after phase 1.

### 6. (v2) Thin wall furniture drifts off its wall — the solver's exploration floor; fixed in core
Shipped v1 with the fireplace **1.6 m off the back wall** while the whole VLM loop read clean — the
user caught it in the blend. `GradSolver.compute_action` gives every object a minimum move score
toward open space scaled by `1/area`, so a thin wall piece (fireplace: 0.24 m deep) random-walks
into the room over the solve; nothing pins wall placements despite the documented intent. Core fix:
`RoomGroup._repin_wall_furniture()` — a deterministic post-solve AABB snap back to the wall
(perpendicular axis only; along-wall drift kept; runs before the doorway pass so doors win). Snap by
world AABB, **not** recomputed `wall_deltas` (rotation-aware `get_whd` double-swaps w/d for
90°-rotated items). The VLM loop never checks wall flushness — verify gaps in the blend.

### 7. (v3) `place_on_top` targets the group ANCHOR — the lamp-on-the-chair bug
`nook.place_on_top(table_lamp)` with the armchair as the nook's anchor seated the lamp on the
chair's CUSHION — the tournament treats any horizontal surface as valid, and no constraint knows
"a lamp doesn't belong on a seat". The side table being in the same group is irrelevant;
`place_on_top` always stacks on the anchor. Fix = the bedroom unit rule: build `side_unit`
(anchor = the TABLE, `place_on_top(lamp)`), then place the unit into the nook. Before any
`place_on_top`/`place_inside`, ask "what is this group's anchor?"

### 8. (v2) Wall art that "faces the other way" = reversed mesh front; compare with the catalog preview
The photo-grid mesh (`future/09f28392…`) hung with its image side INTO the wall — the render showed
its brown backing boards, which read as plausible sepia frames, so `RotationConstraint` stayed
silent. The catalog preview (`3D-FUTURE-images/<id>.png`) shows the true front — which is also four
EMPTY frames. Fixed both ways: `front_cache set <id> 180` (once per asset) and swapped to a collage
with real photo content (`future/e2b0dcb4-c660-415b-8b1e-cddeb905441b`).

## Asset coverage (all off-the-shelf, no ingest)
Fireplaces, sectionals, leather club chairs, ottomans, rustic coffee tables, filled bookcases all
exist in-dataset at good similarity (0.68–0.79). Pinned for palette/form: fireplace, sectional
(cream w/ baked-in accent pillows — no separate cushion props needed), leather chair, ottoman,
coffee table, bookcase, and the known-flat beige wool rug (`hssd/249bbdc…`, the lobby pick). Lamps /
side table / vase / books / plant / photo grid left to retrieval — all resolved on-target first try.
Landscape art reused the bedroom's pinned+pre-scaled id.

Palette: cool light gray walls, dark walnut floor, cream/taupe upholstery, caramel leather, plum
curtain accent, warm brass lamps.
