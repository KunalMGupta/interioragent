# Hospital patient room — worked example

Status: **built & VLM-clean** ("Bed-Centered Healing Inpatient Room",
`scenes/work/hospital_room_v1.py`, seed=42). Final compile: `no rotation / no wall
overlap`, room vote decayed 0.8→0.85→0.94→0.95 (declined ≈ converged) at
`modulate_scale=0.85`. Built through the guided flow (flow_0712_170142_dbf1),
entirely via the MCP tools (post-`reload_credentials`).

## Prompt(s) this covers
- "a hospital (patient/inpatient) room", "a medical ward room", "a clinic recovery
  room with a bed and equipment".

## Plan summary (from the planner)
Bed as the room's focal point with both-side access; wall-mounted monitors + bedside
console; visitor seating by a daylight window; hygiene prep counter with sink;
biophilic softeners (plants, nature graphics, warm wood) over a calm neutral palette;
layered glare-free lighting; easy-clean warm flooring.

## The layout idea: bedroom's hero skeleton, walls purpose-loaded like meeting_room
- BACK = the HEADWALL: the hospital bed hero (RelativeGroup), bedside cabinet on its
  left and the vitals monitor on its right (nightstand pattern), the flat headwall
  gas-outlet strip hung on the wall above the low bed.
- RIGHT = DAYLIGHT/VISITOR: standard window + sheer curtains; visitor nook =
  `AroundGroup` (round table anchor, two chairs `place_arc`ed and **explicitly
  `face()`d at the table**) on a light grey rug.
- LEFT = STAFF/SERVICE: sink vanity center, med supply cart at the bed end,
  wheelchair in the left slot.
- FRONT = door (right) + botanical print center (the patient's sightline) +
  the tall wood wardrobe (left slot).
- Lighting: one flush LED pass, density 0.01.

## Pinned assets (audited previews)
| Role | id | note |
|---|---|---|
| Hospital bed (hero) | `future/280e7e5e-4128-4696-abb8-72744becce48` | rails + attached IV arm; **ships at ~half scale** → `modulate_scale=2.1` (uniform!) |
| Headwall strip | `custom/920037c5376d7f897f7b4b142bea7792e938400d` | ingested; FLAT → safe to `place_on_wall_*` |
| Vitals monitor | `custom/475c4c6d50144e1659d7bbc18121378a897d505e` | ingested; excellent detailed mesh on a rolling stand |
| Wheelchair | `custom/07c9f10971507810789d358c15c1861a4e19a67f` | ingested; instant category cue by the door |
| Med supply cart | `hssd/cc15f4f67e55963a009abe0f4fe10148cb632f2f` | white 3-drawer metal trolley |
| Sink vanity | `future/a521cb7a-d9df-4bc8-a2e2-8dc1e61c4d23` | swapped IN after `hssd/3cc3f058…` floated 0.14 m (off-center origin lint) |

Bedside cabinet / wardrobe / armchairs / side table / plants / botanical print / rug
resolved cleanly from NL queries (home-furniture categories, dataset-strong).

## What worked / gotchas
- **The medical-fixture gap is smaller than the catalog warns** — a real hospital bed
  exists in 3D-FUTURE, and prior ingests (headwall, vitals monitor, wheelchair) carry
  the clinical read. Browse before assuming an ingest round is needed.
- **Uncurated hero rule reconfirmed (garage-car lesson): pin the id AND fix the
  scale.** The bed's native length was 1.0 m; `modulate_scale=2.1` (uniform — never
  `width=` alone, which squashes) gives a true-size bed and puts the attached IV arm
  at a believable ~1.75 m.
- **Floating-mesh lint → swap, don't compensate.** The first sink vanity floated
  0.14 m (off-center origin); swapping to a sibling from the same browse fixed it in
  one build.
- **`place_arc` seating needs explicit `face(chair, toward=anchor)`** — same as
  living_room's flanking chairs. The VLM flagged both chairs once, the render agreed,
  one fix converged it.
- No overbed table mesh exists (the one candidate is a surgical cantilever table —
  reads wrong); bedside cabinet + med cart carry the function. No privacy-curtain
  mesh; window curtains carry the softness. Both logged as ingest candidates.
- **Don't overload a single wall (the general rule this scene minted — user catch).**
  v1 queued wheelchair + wardrobe + vanity + med cart along the left wall; RoomGroup
  grew the depth to fit the queue and the room read oversized no matter the shrink
  votes. Moving the wardrobe to the front wall (and the wheelchair into the vacated
  slot) let the shell converge at `modulate_scale=0.75`, `no rescale`. Full rule in
  workflow/coarse_to_fine.md.
- **The vanity mesh front is REVERSED** (`future/a521cb7a…` — sink face toward the
  wall under the default facing; user catch, the VLM never flagged it). Bad asset,
  not bad code: fixed ONCE with `python -m IDSDL.front_cache set a521cb7a… 180`
  (durable, every future scene inherits it) rather than a per-scene `facing=` hack.
- **This scene minted the wall-object clearance auto constraint** (user catch #3): the
  tall wardrobe stood in front of the botanical print and NO existing signal fired.
  Now automatic in every RoomGroup compile — tall floor furniture is slid along the
  wall out of a wall object's AABB span (see workflow/constraints.md).

## VLM feedback we hit and how we resolved it
- `[Lint] vanity FLOATS 0.14 m` (Ph1) → swapped the mesh → clean.
- `rescale room by 0.8` (Ph1) → `0.85` (Ph2) → held per render-wins-early, applied
  `modulate_scale=0.85` in the final phase → decayed `0.94` → `0.95` → declined
  (≈ noise; the both-side bed access + door approach lanes are functional space).
- `rotate left/right armchair to face the coffee table` (full build) → **accepted**
  (render agreed — arc placement had them angled away); `face()` both at the table →
  `no rotation`.
- Post-redistribution `no rescale` + four rotation votes (`bedside cabinet / sink
  cabinet / wheelchair to face the BED`, `armchairs to face the table` again) →
  **declined all** — wall furniture correctly faces the room, the chairs are already
  faced; the "face the bed" family is the dental-unit noise class. Render confirmed.

## Manual constraints used
- None. Auto overlap/bounds + door clearance + appliance/cabinet category clearances
  sufficed.

## Possible refinements (not blocking)
- Ingest a real overbed table and a privacy-curtain track for a fully clinical read.
- A TV on the footwall (plan mentions one); skipped to keep the footwall art calm.
