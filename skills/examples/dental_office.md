---
id: example:dental_office
kind: example
family: set-piece-hero
category: "dental operatory"
pattern: "Set-piece hero — hang the whole room on one ingested \"unit/set\" asset"
---
> **Digest (from the pattern index):** **Set-piece hero** — hang the whole room on one ingested "unit/set" asset


# Dental office — worked example (single operatory, "set-piece hero asset")

A compact single-room build whose defining lesson is **one ingested asset can be the entire
hero**: a complete dental UNIT mesh (chair + overhead light + delivery + monitor + cuspidor)
carried the scene, so the rest was ordinary dataset retrieval + placement. Read alongside
`../workflow/asset_selection.md` (kickoff) and `../workflow/coarse_to_fine.md`.

## Status

Status: **built** as `scenes/dental_office.py` (seed=35). [`dental_office_v1.py`](dental_office_v1.py)
is that same program, phase-gated (2026-07-13) — lint-clean, **phase-1 build VERIFIED** in the 2026-07-13 verification round (layout signals clean; see [`_VERIFY_NOTES.md`](_VERIFY_NOTES.md) for the round record) (the rotate-vote storm reproduced exactly as documented below — declined).

## Prompt(s) this covers
- "a dental office" / "a dentist exam room / operatory" (pediatric or adult).

## Plan summary
Planner → **"Glass-Partitioned Modern Dental Exam Suite"**: a single operatory, main dental
chair as the focal hub, wood-toned perimeter cabinetry with wipe-clean counters, a
patient-education monitor, a **green accent** + botanical mural to calm anxiety, bright even
recessed ceiling light, a **circular sage floor motif** under the chair, glass entry door +
daylight. Palette: neutral walls, warm wood, soft green, light clinical floor. The retrieved
reference skills were all **Hospital-Room** (nearest library neighbour).

Because the user supplied an **orange pediatric** dental chair, the build leaned into a
**cheerful pediatric operatory** — clinical white + wood + green with the orange chair as the
single pop of colour.

## The crux: the hero asset (do the asset kickoff FIRST)
The dataset has **no true dental treatment chair** — `inspect "a dental examination chair"`
returns a **blue phlebotomy-style exam chair** (arm supports, reads medical-exam not dental)
then salon/barber chairs. That is a textbook "high-impact missing asset with no acceptable
substitute" → have the **user source a free .glb** and **ingest** it (per asset_selection.md).

The supplied `arte_kids_dental_chair.glb` turned out to be a **complete dental UNIT** in one
mesh: reclining chair + overhead exam-light arm + articulated patient monitor +
delivery/instrument tray + cuspidor. **One ingest closed four gaps at once** (chair, light,
delivery, monitor). Lesson: **before assembling a hero from parts, check whether a single
"unit / set" mesh exists** — a dental chair, like a fitted kitchen or a vanity, is often
modeled as a bundled set. Pin it (`asset_id="custom/64a7f627…"`); it also ranks #1 for
"pediatric dental treatment chair unit" so retrieval is safe, but pinning is durable.

Ingest recipe used: `zip` the glb → `python -m IDSDL.ingest chair.zip` (the tool wants a
**zip of glbs**, not a bare .glb). Ingest auto-centered it and VLM-captioned it correctly;
geometry was already Y-up / metric / upright, so **no front-cache fix was needed**.

Everything else was plain dataset retrieval (all rank-1 good): saddle stool
(`hssd/3e5b80fa2791…`), white 3-drawer mobile cart, a **wood bathroom vanity set** as the
sink/prep counter, a tall white cabinet as supply storage, a tall potted plant, framed
botanical + kids prints.

## Skeleton program
A single operatory is **compact/near-square** — unlike the salon, you do NOT load long walls to
stretch the room; balance the four walls and let `modulate_scale` set the final size.

## Program

[`dental_office_v1.py`](dental_office_v1.py) — phase 1 the floor anchors (the central operatory
group, the perimeter cabinetry, the corner workstation and the door), phase 2 the surface dressing
(the desktop layer + the corner plant), phase 3 the wall decor, the glass front wall and the ceiling
light. `workbench run skills/examples/dental_office_v1.py --phase 1` builds the layout alone in
~1–2 min.

## What worked / gotchas
- **A single "unit" mesh beats assembling parts.** The whole operatory came from one ingested
  asset — no need for separate light/delivery/monitor placements (which would have been fiddly
  to pose relative to the chair).
- **Green accent WITHOUT a per-wall texture.** `place_walls` takes ONE `wall_texture` for all
  four walls (no per-wall API). The planner's "green accent wall" was delivered as a **large
  botanical leaf print on the patient-facing back wall** — keep walls soft-white, hang the
  accent. Don't reach for a DSL extension for this.
- **`place_rug` retrieval is unreliable for a *plain* rug** — "a round sage green area rug"
  returned an **ornate floral Persian rug** that wrecked the clinical read. Clinical rooms
  want a **hard floor**; the plan's "circular sage floor motif" is a floor *design*, not a rug.
  **Dropped the rug** rather than fight retrieval. (If a plain accent rug is truly wanted, pin a
  known-good id — NL retrieval favours decorative rugs.)
- **A bathroom vanity set doubles as the sink/prep counter** (cabinet + basin + counter, and it
  bundles a wall mirror). Slightly bathroom-y but a solid clinical prep station; the botanical +
  kids decor keep the room reading dental.
- **Dental units have no canonical room-facing** — `place_on_center(operatory, facing="front")`
  looked correct from every corner; the repeated `RotationConstraint` "rotate … by 180 / to face
  the operator" was noise. Trusted the render (see below).

## VLM feedback we hit and how we resolved it
- **`rotate <unit/stool/cart> by 180 / to face the chair`** (every phase) → **declined.** The
  render read correctly from all four corners; a reclining dental unit has no meaningful
  "front." Classic noisy `RotationConstraint` — eye is the arbiter (`../workflow/vlm_feedback.md`).
- **`rescale room by 0.8` (Ph1) → `0.85` (Ph2)** → **held in Phases 1–2** (occupancy still
  climbing), then applied `RoomGroup(modulate_scale=0.85)` in the **final phase** → returned
  `no rescale`. The "render wins early; act on room size last" rule, again.
- **WallOverlap: `front_wall slot 'right' has Door + Window`** → the **picture window is wide**
  and collided with the door. Swapped `place_window_picture` → `place_window_standard(
  "front_wall", position="left")` (claims only the left slot); door keeps the right slot →
  `no wall overlap`. Lesson: **`place_window_picture` has no `position` and spans wide** — on a
  wall that also has a door, use `place_window_standard` with an explicit non-conflicting slot.

## Add-on: the corner admin workstation (`WorkstationGroup` + `DesktopWorkstationRetriever`)
A later pass added a **charting/admin desk in the back-left corner** — the first use of the new
reusable **`WorkstationGroup`** (desk + operator chair + computer + desk accessories) and its
paired **`DesktopWorkstationRetriever`** (the on-top item pool). Both are general tools (office,
reception, classroom, study), built per `../add-placement-group/SKILL.md`:

```python
FLAT_DESK = "hssd/a42e2ef37ca205ecb1927bde89c6b618ddcda71b"   # flat 0.72 m desk (pinned)
with scene.WorkstationGroup() as station:
    station.set_anchor(scene.AddAsset("a simple flat wooden office desk", asset_id=FLAT_DESK))
    station.place_chair(scene.AddAsset("an ergonomic office chair"))
    station.place_computer(scene.AddAsset("an all-in-one desktop computer"))   # set = monitor+kb+mouse
    station.place_accessories([scene.AddAsset("an articulated desk lamp"),      # <=3 on-top total
                               scene.AddAsset("a small potted succulent for a desk")])
# ... inside the RoomGroup:
    room.place_on_back_left_corner(station, facing="front")
```

Lessons from wiring it in:
- **On-top items MUST go through `place_on_top`, never a hand-computed `y = desk_height`.** v1 of the
  group seated items at the desk's **aabb top** — which floated the monitor, pen cup and plant in
  mid-air (only the lamp, which was actually a desk prop, sat right) the moment the desk wasn't a
  clean flat box. `place_on_top` seats on the highest *substantial* surface (VLM tournament + AABB
  fallback), so items rest on the real writing surface. The group now delegates the desktop layer to
  it. **Corollary:** `place_on_top` is reliable with only **a few** items — the group **caps the
  desktop at 3** (computer + two accessories); pass your best three, don't cram the desk.
- **Pin a FLAT desk.** The default retriever returned a 1.2×**1.48**×0.88 m "desk" (a hutch/back-unit
  that slipped past the flat-top picker rule). Even `place_on_top`'s *AABB fallback* would seat on the
  hutch top; its VLM path handles it, but a flat desk is safest. The group **warns** above 1.05 m; pin
  a ~0.72 m flat desk (`hssd/a42e2ef37…`).
- **The computer is a SET.** Standalone keyboards/mice barely exist in the dataset; querying "an
  all-in-one desktop computer" returns an iMac/VAIO mesh with the monitor+keyboard+mouse together —
  cleaner than trying to assemble three pieces (same "prefer the bundled set" lesson as the dental
  unit and the fitted kitchen).
- **Corner placement + `facing="front"`** put the desk against the back wall with the chair in front;
  clean, no wall-overlap, no rescale. Verified numerically in `tests.py::test_51` and by render.

## v2 polish pass (what a "remake / polish" actually changed)
Three targeted upgrades, each a reusable lesson:
- **Clinical sink counter, not a bathroom vanity.** "a wood bathroom vanity with a sink" routes to
  `BathroomVanityUnitRetriever`, whose sets **bundle a wall mirror** → the corner read *bathroom*, not
  clinic. Fix: **pin a kitchen base-cabinet-with-integrated-sink** (`hssd/048d80c3…`, wood cabinet +
  stainless sink, NO mirror) — a clean handwash/prep counter. Lesson: for a clinical counter, avoid
  the vanity retriever (mirror) and use a kitchen sink cabinet.
- **Glass-partition entry (the plan's glass-suite look).** `place_door` only mounts a **fixed opaque
  door** — there is no glass-door asset. So the "glass entry" is done as a **floor-to-ceiling glass
  front wall** (`place_window_floor_to_ceiling("front_wall")`, which removes that wall → a mullioned
  glass partition) with the **actual door moved to a side wall** (`place_door("left_wall", "right")`).
  Reads as a modern clinical glass wall. **Do NOT add curtains to it:** `curtain="sheer white
  curtains"` renders as **parted opaque drapes with a black gap** (the exterior is unlit) — worse than
  bare glass. Leave the glass bare; the black "night" exterior is a renderer limitation (no exterior
  environment behind an opening) but the clean mullioned glass still reads well.
- **Room rescale is noise once the layout is set.** After opening the wall to glass, `RoomProportions`
  flipped `0.85` (shrink) → `1.1` (enlarge) between versions. A shrink↔grow flip against a good render
  = converged/noisy; **held the size** (render wins).

## Manual constraints used
- None. Auto overlap/bounds + door clearance sufficed for a compact single-operatory layout.
