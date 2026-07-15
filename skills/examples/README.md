# Examples catalogue — pick by the *pattern*, not the name

Each entry is a **pair** — `<name>.md` (the lessons: the pattern, the traps, the VLM votes we
declined) and `<name>_v1.py` (the program: phase-gated, lints, runs). For a new prompt, find the
row whose **layout pattern** matches, then copy its `.py` — don't start from scratch. Most rooms
are a variant of a pattern we've already solved.

The `.py` is the thing you copy; the `.md` tells you what will bite you. See
[`_TEMPLATE.md`](_TEMPLATE.md) before adding one — an example without a runnable program is not
a worked example.

## Worked examples (VLM-iterated, backed by a memory scene-status)

| Example | Category | Layout pattern it teaches |
|---|---|---|
| [dental_office.md](dental_office.md) | dental operatory | **Set-piece hero** — hang the whole room on one ingested "unit/set" asset |
| [bathroom.md](bathroom.md) | spa master bath | Set-assets + width-only scaling + overlap handling for bundled sets |
| [executive_office.md](executive_office.md) | executive office | **Single room, zoned** — a storage backbone splits work vs. |
| [lobby.md](lobby.md) | corporate lobby | **Reception anchor + waiting lounge** — `AroundGroup.place_rectilinear` cluster; |
| [meeting_room.md](meeting_room.md) | conference / boardroom | **Table hub + presentation wall** — a rectilinear chair ring around a stretched table; |
| [dining_room.md](dining_room.md) | family dining room | **Table hub, domesticated** — READ FOR ANY "warm"/"cosy"/mood brief: once phase 3 hangs a fixture, the brightness dial is `scene.light_budget` (fixed 500 W floods a room), NOT the sky — and `IDSDL_SKY` must be exported in the SHELL, it is a no-op inside the program under workbench too |
| [computer_room.md](computer_room.md) | computer lab | **Repeated-unit grid** — a `WorkstationGroup` tiled across the floor |
| [locker_room.md](locker_room.md) | locker room | **Long rows** — flush-on-wall or down the centre (never `place_on_<side>`) |
| [warehouse.md](warehouse.md) | industrial storage | Racking **rows in room-thirds** to carve forklift aisles |
| [gym.md](gym.md) | gym (3 sizes) | **Large perimeter multi-zone** — zone first, cardio faces the view, mirror wall |
| [greenhouse.md](greenhouse.md) | greenhouse / conservatory | **Daylit glazed nave** — twin bench runs lining floor-to-ceiling glass + a centre bench spine; — READ FOR ANY WINDOW OR "bright"/"sunlit" BRIEF: the "black window void" and the "black ceiling" were ONE renderer bug (transparent film) and are now FIXED — glaze freely, the old void workarounds are obsolete; and brightness is a SKY setting, never `add_lighting` (fixed 500 W / N) |
| [casino.md](casino.md) | gaming floor | Large multi-zone — table hub + repeated slot rows + bar |
| [game_room.md](game_room.md) | rec lounge | **Hero-in-the-middle** — the hero's clearance sizes the room; |
| [hair_salon.md](hair_salon.md) | hair salon | **Motif-group build** — `MirrorStationGroup` styling row; |
| [bar.md](bar.md) | cocktail bar | Focused cluster — a straight bar-line + back-bar; |
| [restaurant.md](restaurant.md) | bistro dining room | **Zoned single room** — bar wall + banquette wall + a field of 2-top clusters; |
| [library.md](library.md) | reading hall | **Symmetric corridor** — twin shelf rows on the long walls + a centre reading-table column; |
| [retail_store.md](retail_store.md) | apparel boutique | **Central spine + perimeter loop** — twin double-sided rails frame a display table; |
| [jewelry_shop.md](jewelry_shop.md) | fine-jewelry boutique | **Show the PRODUCT, not the fixtures** |
| [bedroom.md](bedroom.md) | master bedroom | Core residential — **symmetric hero** (bed) + a self-contained reading-nook sub-group |
| [children_room.md](children_room.md) | kids bedroom | Three small zones; |
| [nursery.md](nursery.md) | nursery / baby room | **Four walls, four jobs, an empty middle** — READ FOR ANY PALE OR PASTEL ROOM: an all-white room is an EXPOSURE trap — a big window + the default sky 3 |
| [florist_shop.md](florist_shop.md) | flower shop | **Mass ONE abundant prop** — bouquets on six repeated `bloom_table`s carry the identity; |
| [toy_shop.md](toy_shop.md) | toy / comic / book shop | **PRE-STOCKED shop fixtures** — (via `ShopFixtureRetriever`) carry the identity — don't crown empty/wrong shelves; |
| [coffee_shop.md](coffee_shop.md) | café / coffee shop | **Compact service spine + 2-top field** |
| [hospital_room.md](hospital_room.md) | inpatient room | **Hero bed + purpose-loaded walls** |
| [bakery.md](bakery.md) | bakery / patisserie | **Service wall + glass-front perch** — white counter + stocked mid-height wire rack as ONE station; |
| [laundromat.md](laundromat.md) | small laundromat | **One heavy service wall** — a mixed-type `GridGroup` row (washers + rolling cart + dryers) flush on the back wall; |
| [living_room_cozy.md](living_room_cozy.md) | cozy living room | **Hearth focal wall + facing conversation cluster** |
| [residential_variations.md](residential_variations.md) | bedroom / living / dining / bath / kitchen / study | **The variation + REVIEW round (2026-07-14)** |
| [classroom.md](classroom.md) | classroom | **Repeated-unit grid, bare-desk variant** |
| [clothing_store.md](clothing_store.md) | apparel boutique (fashion) | **TRUE-SIZE SHOP FITTINGS** — READ FOR ANY SCENE BUILT ON INGESTED FIXTURES. Also: the persistent "shrink the room" vote was a symptom of toy-sized furniture, not a big box |
| [closet.md](closet.md) | walk-in closet / dressing room | **Narrow corridor with DEEP cabinetry both sides — the camera rule applied at DESIGN time** — READ FOR ANY NARROW ROOM WITH LOADED LONG WALLS (closet, pantry, galley, utility, archive) |
| [grocery_store.md](grocery_store.md) | grocery store / supermarket | **Produce-first shop — and the two STRUCTURAL rules every scene needs.** |
| [bookstore.md](bookstore.md) | indie bookstore | **Retail spine + perimeter loop, book edition** |
| [operating_room.md](operating_room.md) | operating room / surgical suite | **Hero-in-the-middle, sterile** — the operating table's 1.2 m sterile RING sizes the room (game_room's clearance rule); — READ BEFORE INGESTING ANY USER-SUPPLIED GLB ZIP: a raw zip is not ingest-ready and breaks SILENTLY three ways — multi-mesh (loader keeps mesh[0] → renders DISASSEMBLED |
| [corridor.md](corridor.md) | corridor / hallway | **Pure passage — the empty center lane IS the scene** |
| [music_studio.md](music_studio.md) | recording studio | **Two zones on the centerline** |
| [tv_studio.md](tv_studio.md) | TV studio / news set | **Hero set-piece facing a CAMERA LANE** |
| [prison_cell.md](prison_cell.md) | prison / jail cell | **The SUBTRACTIVE room — austerity IS the design** |
| [office_modern.md](office_modern.md) | modern private office | **ONE hero zone + a corner-split storage backbone** |
| [kindergarten.md](kindergarten.md) | kindergarten / preschool | **Hero ON THE FLOOR — the rug IS the anchor** |
| [kitchen.md](kitchen.md) | kitchen | **SET-PIECE: build a kitchen on ONE complete fitted kitchen UNIT — never assemble it from parts — and ALIGN IT TO A CORNER.** |
| [laboratory.md](laboratory.md) | research / teaching wet lab | **Repeated-unit grid + clinical perimeter — and the sharpest statement yet of "the grid is not the category, the PRODUCT is"** |
| [waiting_room.md](waiting_room.md) | clinic / office waiting room | **Two facing seat banks + a reception anchor** |
| [fast_food.md](fast_food.md) | fast food / burger joint | **The category whose every FIXTURE is missing — and it still reads** |
| [wine_cellar.md](wine_cellar.md) | wine cellar / tasting room | **READ FOR ANY DIM BRIEF (cellar, bar, cinema, speakeasy).** — READ FOR ANY DIM BRIEF (cellar, bar, cinema, speakeasy). Layout is the library corridor verbatim (twin stocked rack runs on the long walls + a central tasting table) — zero layout iterations |
| [art_studio.md](art_studio.md) | art studio / painter's loft | **The TOOL-IN-USE room: the hero is a gap, and the picker's rank-1 is its TOY version.** |

| [laundry_room.md](laundry_room.md) | home laundry / utility room | **Fix the SHELL with SLOTS, not `modulate_scale` — the transferable version of the footprint rule.** |
| [pantry.md](pantry.md) | pantry / walk-in larder / dry store | **You CANNOT densely stock a tall rack with `place_inside` — adding goods makes it EMPTIER, and that inverts jewelry_shop's instinct.** |
| [museum.md](museum.md) | museum / grand exhibit hall | **The INGEST-FIRST room, at hall scale: identity is 100% the EXHIBITS, and the hero commands by standing ALONE.** |
| [resto_kitchen.md](resto_kitchen.md) | restaurant / commercial kitchen | **Recipe-B is CORRECT for a COMMERCIAL kitchen — and the camera-height rules, tripped twice in one scene.** |
| [living_room.md](living_room.md) | living room (warm modern) | **Facing seating cluster around a coffee table** |
| [garage.md](garage.md) | garage / car workshop | **Cluster composition, not scattered props** |

## Adding a new one

Copy [_TEMPLATE.md](_TEMPLATE.md). A worked example should record the final skeleton, the zone map,
and each VLM-feedback→action you took. Then add its row above and cross-link the memory
scene-status.
