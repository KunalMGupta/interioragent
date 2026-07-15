---
id: example:tv_studio
kind: example
family: hero-anchor-room
category: "TV studio / news set"
pattern: "Hero set-piece facing a CAMERA LANE"
---
> **Digest (from the pattern index):** **Hero set-piece facing a CAMERA LANE** — the anchor desk + a `GridGroup` seat row behind it sits in the back floor slot facing front; the camera on its tripod and the key/fill light stands are room-level floor objects with `facing="back"`, so the whole lane aims at the set (nesting them in a group bakes ±90° and turns a light's back to the anchors). Teaches **hunt a gap-category hero by SILHOUETTE, not caption** (no broadcast camera or softbox exists — an "antique camera with a tripod" and a "floor lamp with a tripod base" ARE the studio camera and the light stands), and the sharpest wall-hanging lesson yet: **freeform caps the whole run at 50% of the wall while the slots mount LOW enough to be occluded by your own furniture** (both paths tried; the slot path cascaded two wall-clearance warnings) ⇒ **a wall-hung backdrop cannot be made big — a full-height backdrop is a floor asset, not wall art**. Also: `modulate_scale` is a **no-op on `place_on_top` items** (the tournament height-fits them)


# TV studio — worked example (news/talk-show set: hero set-piece facing a camera lane)

Status: **built & VLM-clean** (`scenes/work/tv_studio.py`, seed=42, converged in 2 phase builds +
3 full renders). Final compile: `no rescale`, `no rotation`, `no wall overlap`, no `[Lint]`/WARNING
lines. Program copy beside this file: `tv_studio_v1.py`.

## Prompt this covers
- "a TV studio / news set / talk-show set: anchor desk, camera on a tripod, studio lighting,
  monitors, a backdrop", "a broadcast set", "a podcast/interview set" (drop the monitors, add a
  second seat pair).

## Plan summary (from the planner)
"Anchor-Centric Curved Desk Studio Core" — a curved anchor desk as the production hub, two large
monitors flanking it, a geometric backdrop with hexagonal acoustic panels, a gear rack, a camera on
a tripod, cool grey + blue accents against warm wood, layered studio light.

## The layout idea: a HERO SET-PIECE facing a CAMERA LANE
This is meeting_room's focal wall crossed with music_studio's centerline zoning — but the second
zone is not furniture, it is **the lane the camera shoots down**:
- **BACK (floor slot) = the SET**: the curved anchor desk + a two-seat `GridGroup` row of anchors
  tucked behind it, on a dark carpet. `place_on_back(anchor_set, facing="front")` — the desk's
  facade turns to the camera and the anchors look across it.
- **BACK WALL = the BACKDROP**: two monitors flanking a geometric panel, one
  `place_on_wall_freeform` run.
- **FRONT = the CAMERA LANE**: the camera on its tripod on the centerline, key + fill lights on
  stands flanking it — all three placed at room level with `facing="back"`, so every one of them
  aims at the set.
- **RIGHT WALL = the gear spine** (a stocked rack, off-center); side walls carry one acoustic panel
  each; **FRONT wall = the door**. **No windows** — a studio is blacked out, which also dodges the
  renderer's black-void window limit entirely.

## Asset audit (gate 3) — the three gaps, and why none of them blocked
The dataset is home-furniture-biased and broadcast gear is the worst case. **All three heroes are
substitutes, and all three read correctly — because the SILHOUETTE is what sells them at room scale:**
- **No professional broadcast camera.** "a professional video camera on a black tripod" returns
  telescopes, tripod *lamps* and handheld camcorders. The only true camera-on-tripod mesh is
  `hssd/6d5c2629…`, captioned *"antique metal camera with a tripod, serving as a decorative…"* — in
  the render it is a boxy body + lens + film reels on a splayed tripod, i.e. **more convincingly a
  studio camera than its caption suggests**. Pinned, then scaled to a real 1.5 m
  (`cam.scale(cam.get_width()*1.5/cam.get_height())`).
- **No softbox / LED panel on a light stand.** `hssd/4c5ab0e1…` ("black standing floor lamp with a
  **tripod base**") is a tilted dish head on a tripod — the exact studio-light silhouette. Two of
  them (key + fill) at 1.85 m are the single strongest studio cue in the room.
- **No news desk.** `future/8f7519b8…` is a curved **solid-front** desk (closed modesty panel);
  stretched to `width=2.4` it is an anchor desk.
> Lesson: **when a gap-category hero is missing, hunt by SILHOUETTE, not by category name** — and
> eyeball the mesh (`show n --big`), because a dismissive caption ("antique", "decorative", "floor
> lamp") hides the right shape. Reading the caption alone would have sent this scene to ingest.

## What worked / gotchas
- **The anchors go BEHIND the desk as a `GridGroup` ROW, not on the desk's diagonals.** v1 used
  `place_on_back_left/right` → the two chairs were stranded out at the desk's *ends* (they are
  corner placements, offset by half the anchor's width). Fix: build the pair as
  `GridGroup.place_row([chair_l, chair_r])`, then `place_on_back_adjacent(seat_pair)` +
  `face(seat_pair, toward=desk)` — one tucked, correctly-facing anchor row.
- **Aim the lane at the set with `facing` + `face()`, not with a group.** v1 nested the lights in a
  `RelativeGroup` around the camera (`place_on_left_further/right_further`) — those verbs bake ±90°,
  so one dish turned its **black back** to the anchors. Fix: place the camera and both lights as
  room-level floor objects with `facing="back"`, **then `room.face(light, toward=desk)` on each**.
  `facing="back"` alone only squares them to the back WALL, which from the lane's left/right corners
  still points a dish past the anchors; `face()` runs at the end of compile off the settled positions
  and angles each dish IN at the desk — the real key/fill pose. (User catch: the VLM said
  `no rotation` throughout, both before and after. A dish aimed 30° wide of the talent is not a
  *rotation* error the constraint can see — same class as the reversed-front vanity.)
- **An orientation-sensitive `place_on_top` prop needs its own `face()`.** The anchor's laptop had
  its screen turned to the camera (i.e. away from the person using it) — `place_on_top` sizes and
  seats an item but never *aims* it. `anchor_set.face(laptop, toward=seat_pair)` (computer_room's
  monitor rule). Verify by eye: from the room-front camera you should see the laptop's **lid**.
- **Don't put the mic mesh on the desk at all.** The only mic is a FLOOR mic-on-stand; on the desk
  the tournament height-fits it to the anchor and you get two oversized black lollipops that
  `modulate_scale` cannot shrink (see below). Dropped — the desk reads fine on laptop + mug.
- **Stock the rack** (`place_inside`) — an empty rack names the fixture, not the studio.
- **Offset the rack from the wall center** (`place_on_right_wall_left`): at 1.8 m it would sit inside
  the right wall's interior camera and blind that view (bakery rule).

## The back-wall trap (the real lesson of this scene)
**`place_on_wall_freeform` caps the WHOLE run at 50% of the wall width** (`groups.py:2052`), so N
items are shrunk to share half a wall — three items on a 4.5 m wall come out ~0.75 m each, and any
`modulate_scale` you passed is thrown away. The **slots** (`place_on_wall_back_left/center/right`)
hang bigger (`target_width = WIDTH/3 * 0.6`) — but they mount **LOW**, and that is a trap of its own:
1. Slots mount at `(WALL_FURNITURE_HEIGHT_MAX + WALL_MID_LEVEL_MAX)/2`; the panel's bottom edge fell
   **below the anchors' chair-backs**, so the wall-object clearance pass tried to slide the whole set
   out of the panel's span, failed, and emitted
   `[RoomGroup] WARNING: 'RelativeGroup' occludes wall-hung …` — then **cascaded** a second warning
   onto the *left-wall* panel (it had slid the set sideways into that one).
2. Trying to win the width back by standing the set **flush** to the wall
   (`place_on_back_wall_center(anchor_set)`, so the panel would be support-anchored and inherit the
   desk's 2.4 m width) produced the SAME occlusion warning — the chair-backs are simply taller than
   the panel's bottom edge.
→ **Settled on freeform** (mid-wall mount, clears the set) and accepted a modest backdrop.
**General rule: a wall-hung backdrop cannot be made big.** `wall_obj_scale_computer` penalizes
heights over ~1 m by `10*(h-1)²`, so *no* hung mesh becomes a floor-to-ceiling LED wall. If a scene
truly needs a full-height backdrop, that is a **floor-standing asset (or an ingest)**, not wall art.

## VLM feedback we hit and how we resolved it
- **Room size:** `0.8` (Ph1) → `0.8` / `0.82` (Ph2) — unidirectional and stable, and the render
  agreed the walls read empty. Held per render-wins-early, applied ONE decisive
  `modulate_scale=0.82` (*at* the vote, bakery-style, not above it) in the final phase →
  immediate `no rescale`. No oscillation.
- **Everything else was clean by construction:** `no rotation` / `no wall overlap` on every build —
  `facing="back"` on all three lane pieces, the seat row explicitly `face()`d, `facing` omitted on
  all wall furniture, door and wall fixtures in disjoint slots.
- **`modulate_scale` is a NO-OP on `place_on_top` items.** The desk mics looked oversized;
  `modulate_scale` 0.45 → 0.3 changed nothing visible, because the smart-placement tournament
  **height-fits each item to a fraction of the anchor** and overrides the incoming scale. Don't burn
  a build fighting it — either accept the tournament's size or pin a different mesh.
- **Retrieval swap:** "a stack of papers and a coffee mug" → a **multicolored Post-it blob**. Reworded
  to "a white ceramic coffee mug" (one object, material + color).

## Manual constraints used
- None. Auto overlap/bounds + the door's auto-clearance sufficed; the camera lane is natural circulation.
