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
| [meeting_room.md](meeting_room.md) | conference / boardroom | **Table hub + presentation wall** — a rectilinear chair ring around a stretched table; four walls each get a job (present / service / glass / art+door). Stress test; reversed-front-sideboard facing flip; boardroom lighting = one pendant + daylight (panels starfield) |
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
| [jewelry_shop.md](jewelry_shop.md) | fine-jewelry boutique | **Show the PRODUCT, not the fixtures** — a shop reads by its merchandise at viewing height: MASS jewelry props (gold stands / gems / cloches) on a central display table + cash-wrap + window pedestals; keep glass vitrines a thin backdrop. Teaches "empty fixtures don't name the shop" + "VLM loop verifies geometry, not category legibility (human gut-check retail)" + pool-routing reword + pin-for-palette |
| [bedroom.md](bedroom.md) | master bedroom | Core residential — **symmetric hero** (bed) + a self-contained reading-nook sub-group |
| [children_room.md](children_room.md) | kids bedroom | Three small zones; `place_inside` tile-fit |
| [florist_shop.md](florist_shop.md) | flower shop | **Mass ONE abundant prop** — bouquets on six repeated `bloom_table`s carry the identity; opens with a retrieval **stress test**; storefront window + side door; asset-mesh traps (black étagère / baked-in books) |
| [toy_shop.md](toy_shop.md) | toy / comic / book shop | **PRE-STOCKED shop fixtures** (via `ShopFixtureRetriever`) carry the identity — don't crown empty/wrong shelves; perimeter ring + play island + teepee/bean-bag nooks + checkout. Forced out a core `object.scale()` fix + **scale-by-height** for fixtures; teaches `place_on_top`-breaks-on-flat-surfaces and **caption≠mesh (eyeball the preview)** |
| [coffee_shop.md](coffee_shop.md) | café / coffee shop | **Compact service spine + 2-top field** — SLOT ECONOMY for a small/cozy brief (3 floor slots, modest hero widths ⇒ the shell auto-sizes café-scale); massed PASTRIES at viewing height instead of a nonexistent display-case mesh; teaches the off-center-origin floating-mesh trap (swap, don't fight) + sub-0.02 `add_lighting` density for small rooms |
| [hospital_room.md](hospital_room.md) | inpatient room | **Hero bed + purpose-loaded walls** — bedroom's hero skeleton with meeting_room's wall jobs (headwall = equipment, window wall = visitor nook, entry wall = sink/storage); ingested medical meshes (headwall/monitor/wheelchair) carry the clinical read; teaches "uncurated hero: pin id + UNIFORM rescale" (half-scale bed → 2.1×) + floating-vanity mesh swap + `place_arc` chairs need explicit `face()` |
| [bakery.md](bakery.md) | bakery / patisserie | **Service wall + glass-front perch** — white counter + stocked mid-height wire rack as ONE station; the counter top IS the pastry display (no display-case mesh — mass the product); window-bar console + stool row pinned to the storefront via `place_on_front_wall_center` (a front SLOT drifts); teaches the **~1.4 m camera-height ceiling for wall-center fixtures** (taller = a swallowed interior view + hallucinated rotation flags) + squat-mesh scaling (uniform to height, then `scale_only_*`) + "texture retrieval was right, the renderer pales it — check the match before rewording" |
| [laundromat.md](laundromat.md) | small laundromat | **One heavy service wall** — a mixed-type `GridGroup` row (washers + rolling cart + dryers) flush on the back wall; folding counter + waiting nook on the side walls, centre aisle clear; appliance clearance comes FREE from `CategoryClearanceConstraint`; teaches "a genuinely SPARSE room may shrink below 1.0" (two-step final-phase convergence 0.85→0.75) + art-over-a-LOW-run |
| [living_room_cozy.md](living_room_cozy.md) | cozy living room | **Hearth focal wall + facing conversation cluster** — sectional `facing="back"` at the wall-center fireplace (clearance FREE via `CategoryClearanceConstraint`), gallery art stacked above it; leather chair+ottoman+table+lamp nook as one faced sub-group; teaches corner-vs-straight mesh form (phase-1 catch), rug `size` ≤0.8 for a room-dominating cluster, "a room-size vote that never flips is signal — one final-phase application converges", and forced out the core `_repin_wall_furniture` fix (thin wall furniture drifted off its wall via the solver's exploration floor — VLM-invisible, user-caught) + reversed-front wall art (front-cache 180 + compare the catalog preview) |
| [classroom_v1.md](classroom_v1.md) | classroom | **Repeated-unit grid, bare-desk variant** — ONE `place_desk_chair` unit `6 *`-duplicated into a `GridGroup` facing the teaching wall (`face(grid, toward="front_wall")` — the OPPOSITE of a WorkstationGroup grid); teacher desk front-left faced at the class; identity via notebooks/globe/map at surface height; teaches "an accent color the texture library lacks: drop it, don't smuggle it into the wall string" + rescale-oscillation-equals-converged |
| [bookstore.md](bookstore.md) | indie bookstore | **Retail spine + perimeter loop, book edition** — stocked honey bookcase runs on both long walls (library's twin runs) + a centre spine of **double-sided face-out book displays** framing the aisle (retail rail pattern) + a hero new-releases table massed with book stacks; pastel pin-for-palette reading nook; checkout `facing="back"` sees the door. Teaches "the pre-stocked fixture IS the product" at full strength + a ~56 m² lighting-density point (0.015, not 0.04) + decaying-rescale-vote-equals-converged |
| [corridor.md](corridor.md) | corridor / hallway | **Pure passage — the empty center lane IS the scene** — both LONG walls loaded (gallery prints + console/mirror one side, a LOW dressed green cabinet run the other), short walls light, nothing in the center; teaches "the VLM shrink vote never goes quiet on a corridor — decline the residual" (0.75 cramped → 0.85 converged), scale-by-height for wardrobe-tall wall furniture, and "no b/w checkerboard texture exists — drop the accent" |
| [music_studio.md](music_studio.md) | recording studio | **Two zones on the centerline** — a control-zone hero unit (mixer + flanking `face()`-angled monitors + sweet-spot chair, one rug) faces a live zone (drums + mic stands) down the room axis; guitar `GridGroup` line on a side wall; acoustic panels massed via `place_on_wall_freeform`; teaches gap-category hero pinning (mixer-on-stand over the picker's DJ table), the desirable SET (guitar+amp), stock-the-rack, and "red accent via textiles when the wall texture won't cooperate" |

## Early skeletons (pre-workflow, thin — rebuild candidates, don't cite as reference)

These predate the planner-first / VLM-feedback loop and were never properly iterated. Use only for
rough DSL shape; prefer a worked example above.

| Example | Category |
|---|---|
| [living_room.md](living_room.md) | living room (superseded by the worked [living_room_cozy.md](living_room_cozy.md)) |
| [classroom.md](classroom.md) | classroom (superseded by the worked [classroom_v1.md](classroom_v1.md)) |
| [kitchen.md](kitchen.md) | kitchen (has the later `kitchen-set-asset` note; skeleton itself is thin) |

## Pending

- **garage** — garage workshop (car hero + work-zone cluster + storage run); built & VLM-clean,
  distillation lands with the garage commit.

## Adding a new one

Copy [_TEMPLATE.md](_TEMPLATE.md). A worked example should record the final skeleton, the zone map,
and each VLM-feedback→action you took. Then add its row above and cross-link the memory
scene-status.
