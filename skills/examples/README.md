# Examples catalogue — pick by the *pattern*, not the name

Each file is a worked recipe: the finished skeleton for one scene type plus what we changed and
why (especially how we acted on VLM feedback). For a new prompt, find the row whose **layout
pattern** matches — copy that skeleton, don't start from scratch. Most rooms are a variant of a
pattern we've already solved.

## Worked examples (VLM-iterated, backed by a memory scene-status)

| Example | Category | Layout pattern it teaches |
|---|---|---|
| [dental_office.md](dental_office.md) | dental operatory | **Set-piece hero** — hang the whole room on one ingested "unit/set" asset |
| [bathroom.md](bathroom.md) | spa master bath | Set-assets + width-only scaling + overlap handling for bundled sets |
| [executive_office.md](executive_office.md) | executive office | **Single room, zoned** — a storage backbone splits work vs. lounge zones |
| [lobby.md](lobby.md) | corporate lobby | **Reception anchor + waiting lounge** — `AroundGroup.place_rectilinear` cluster; retrieval stress-test + reception-desk ingest; `add_lighting` count math |
| [computer_room.md](computer_room.md) | computer lab | **Repeated-unit grid** — a `WorkstationGroup` tiled across the floor |
| [locker_room.md](locker_room.md) | locker room | **Long rows** flush-on-wall or down the centre (never `place_on_<side>`) |
| [warehouse.md](warehouse.md) | industrial storage | Racking **rows in room-thirds** to carve forklift aisles |
| [gym.md](gym.md) | gym (3 sizes) | **Large perimeter multi-zone** — zone first, cardio faces the view, mirror wall |
| [casino.md](casino.md) | gaming floor | Large multi-zone — table hub + repeated slot rows + bar |
| [game_room.md](game_room.md) | rec lounge | **Hero-in-the-middle** — the hero's clearance sizes the room; zones ring it |
| [hair_salon.md](hair_salon.md) | hair salon | **Motif-group build** — `MirrorStationGroup` styling row; canonical coarse-to-fine |
| [bar.md](bar.md) | cocktail bar | Focused cluster — a straight bar-line + back-bar; compact-group lighting |
| [restaurant.md](restaurant.md) | bistro dining room | **Zoned single room** — bar wall + banquette wall + a field of 2-top clusters; opens with a retrieval STRESS TEST; cafe-SET retrieval trap |
| [library.md](library.md) | reading hall | **Symmetric corridor** — twin shelf rows on the long walls + a centre reading-table column; retrieval stress-test kickoff; `add_lighting` size↔count coupling |
| [retail_store.md](retail_store.md) | apparel boutique | **Central spine + perimeter loop** — twin double-sided rails frame a display table; branded service wall; front-window mannequins. Opens with a retrieval **stress test**; lighting-density-vs-floor-area + storefront-void lessons |
| [bedroom.md](bedroom.md) | master bedroom | Core residential — **symmetric hero** (bed) + a self-contained reading-nook sub-group |
| [children_room.md](children_room.md) | kids bedroom | Three small zones; `place_inside` tile-fit |

## Early skeletons (pre-workflow, thin — rebuild candidates, don't cite as reference)

These predate the planner-first / VLM-feedback loop and were never properly iterated. Use only for
rough DSL shape; prefer a worked example above.

| Example | Category |
|---|---|
| [living_room.md](living_room.md) | living room (core residential — worth a proper rebuild) |
| [classroom.md](classroom.md) | classroom |
| [kitchen.md](kitchen.md) | kitchen (has the later `kitchen-set-asset` note; skeleton itself is thin) |

## Pending

- **garage** — garage workshop (car hero + work-zone cluster + storage run); built & VLM-clean,
  distillation lands with the garage commit.

## Adding a new one

Copy [_TEMPLATE.md](_TEMPLATE.md). A worked example should record the final skeleton, the zone map,
and each VLM-feedback→action you took. Then add its row above and cross-link the memory
scene-status.
