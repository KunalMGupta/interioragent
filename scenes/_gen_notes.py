"""Generate scenes/notes/<name>.md review notes from a structured table.
Run: python scenes/_gen_notes.py    (writes one note per category)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(HERE, "notes")

# name: (pattern, jitter/randomness used, review focus, gap risk + risky assets)
DATA = {
"bedroom": ("Relative bed + flanking nightstands + lamps-on-top; wardrobe/dresser on walls",
    "RoomGroup randomness=0.2", "lamps sized to nightstands; wardrobe vs dresser scale", "LOW"),
"living_room": ("Relative U-seating + rug + on-top tray; bookshelf, plants, window, art",
    "RoomGroup randomness=0.25", "flanking chairs face the coffee table; plant corners", "LOW"),
"children_room": ("Relative bed + play rug; PileGroup of toy bins; toy/book shelves",
    "RoomGroup randomness=0.25; Pile scatter", "toy-bin pile relax; kid-scale bed", "MED — kids furniture"),
"game_room": ("Relative pool table (light); Around lounge arc; arcade cabinets; wall TV",
    "Around jitter=0.5; RoomGroup randomness=0.25", "pool table retrieval; arcade cabinets", "HIGH — pool/arcade"),
"laundromat": ("Grid rows of washers/dryers on walls; Relative folding table (light); chair row",
    "GridGroup gaps", "washer/dryer rows vs wall; machines retrieval", "HIGH — laundry machines"),
"dining_room": ("Around table + chairs rectilinear; on-top runner; rug; sideboard",
    "Around jitter=0.5; RoomGroup randomness=0.2", "chair spacing/jitter realism; chandelier", "LOW"),
"prison_cell": ("Small bare room; bunk on wall; toilet-sink combo; fixed desk+stool",
    "randomness=0 (intentional)", "modulate_scale=0.7 room size; sparse correctness", "HIGH — bunk/toilet-sink/cell"),
"gym": ("Grid of treadmills facing wall; Relative bench (light); Pile of exercise balls",
    "GridGroup randomness; Pile; RoomGroup randomness=0.2", "treadmill grid facing; mirror wall", "HIGH — gym machines"),
"garage": ("Relative workbench (light); StackGroup tyres; PileGroup boxes; tool chest/shelf",
    "Pile scatter; RoomGroup randomness=0.3", "tyre stack; box pile relax; pegboard mount", "MED — workshop props"),
"nursery": ("Relative crib + rug (light); changing table, rocking chair, toy shelf",
    "RoomGroup randomness=0.15", "crib retrieval; pastel feel", "MED — baby furniture"),
"waiting_room": ("Grid rows of linked chairs on walls; Relative coffee table (light); reception",
    "RoomGroup randomness=0.15", "linked-chair rows; reception desk", "MED — linked seating"),
"bathroom": ("Relative vanity (light) + bath mat; toilet/tub on walls; mirror mounted",
    "RoomGroup randomness=0.1", "fixtures vs walls; tub/toilet retrieval", "MED — sanitaryware"),
"art_studio": ("Around easels circle (heavy jitter) + on-top supplies; storage; canvases; big window",
    "Around jitter=0.7; RoomGroup randomness=0.3", "easels retrieval; informal scatter", "MED — easels"),
"kindergarten": ("Around low tables + tiny chairs (×2); Pile toy bins; cubbies/books",
    "Around jitter=0.5; RoomGroup randomness=0.3", "kid-scale tables/chairs; cheerfulness", "MED — kids furniture"),
"locker_room": ("Grid locker rows on walls; Relative bench (light); 2nd bench; mirror",
    "RoomGroup randomness=0.1", "locker rows flush to walls; bench facing", "HIGH — lockers"),
"music_studio": ("Relative mixing console (place_desk_chair) + flanking monitors (light); drum kit; piano",
    "RoomGroup randomness=0.2", "console pose via place_desk_chair; monitors", "HIGH — studio gear"),
"resto_kitchen": ("Grid stainless prep tables; Relative island (light); range/fridge/shelf walls",
    "GridGroup randomness=0.1; RoomGroup randomness=0.1", "commercial steel fixtures retrieval", "HIGH — commercial kitchen"),
"office": ("Grid of desk_unit (place_desk_chair); light_anchor plant; cabinets/shelf; whiteboard",
    "GridGroup randomness=0.4; RoomGroup randomness=0.2", "desk grid facing; whiteboard mount", "LOW"),
"laboratory": ("Grid of bench+stool+microscope stations; light_anchor cart; fume hood; glassware shelf",
    "GridGroup randomness=0.2; RoomGroup randomness=0.2", "lab benches/fume hood retrieval", "HIGH — lab fixtures"),
"pantry": ("Small room; Grid shelf rows on walls; Relative worktable (light); step stool",
    "RoomGroup randomness=0.1", "modulate 0.8 small room; stocked shelves", "MED — stocked shelving"),
"closet": ("Small room; Relative ottoman (light) + rug; wardrobes on walls; mirror; shoe rack",
    "RoomGroup randomness=0.1", "modulate 0.85; open-wardrobe retrieval", "MED — open wardrobes"),
"lobby": ("Around sofas+chairs rectilinear + rug (light); reception desk; tall palms; big art",
    "Around jitter=0.4; RoomGroup randomness=0.2", "modulate 1.25 spaciousness; reception", "LOW"),
"wine_cellar": ("Around tasting table+stools circle (light); StackGroup barrels; wall wine racks",
    "Around jitter=0.35; RoomGroup randomness=0.1", "wine racks; barrel stack; moody stone", "MED — wine racks/barrels"),
"meeting_room": ("Around conference table + chairs rectilinear (light); credenza; wall display",
    "Around jitter=0.4; RoomGroup randomness=0.3", "VALIDATED — good. chairs jitter realism", "LOW"),
"kitchen": ("Around island + bar-stool arc (light) + fruit bowl; range/fridge/cabinets",
    "Around jitter=0.3; RoomGroup randomness=0.15", "island+stools; wall cabinets mount", "LOW"),
"bar": ("Around bar counter + stool row (light); Around lounge circle; back-bar shelf",
    "Around jitter=0.4; RoomGroup randomness=0.2", "stool row along counter; bottles shelf", "MED — bar fixtures"),
"museum": ("Grid pedestals + sculptures on top; Relative bench (light); huge wall art",
    "RoomGroup randomness=0.1", "pedestal+sculpture stacks; spacious modulate 1.2", "MED — pedestals/sculpture"),
"warehouse": ("Grid pallet racking aisles; Pile boxes; Relative packing bench (light); high bay",
    "RoomGroup randomness=0.25", "modulate 1.4 + near-square aspect limit; racking", "HIGH — racking/industrial"),
"casino": ("Grid slot machines; Around card table + chairs arc; bar; neon",
    "Around jitter=0.5; RoomGroup randomness=0.25", "slot machines + card table retrieval", "HIGH — casino gaming"),
"hair_salon": ("Grid styling-chair row facing mirror wall; basin row; reception (light); mirrors",
    "RoomGroup randomness=0.15", "styling chairs face back wall; basins", "HIGH — salon fixtures"),
"classroom": ("Grid desk_units facing front; teacher desk (light); green chalkboard; storage",
    "GridGroup randomness=0.35; RoomGroup randomness=0.15", "grid faces chalkboard; uses custom board query", "LOW"),
"video_store": ("Grid media-shelf aisles; Pile beanbags; checkout (light); posters",
    "RoomGroup randomness=0.2", "media shelves retrieval; posters mount", "MED — media shelving"),
"corridor": ("Relative console runner (light); bench+plant; wall art; doors both ends",
    "RoomGroup randomness=0.15", "ASPECT LIMIT — won't be truly long/narrow (see NOTES #2)", "LOW (layout, not assets)"),
"operating_room": ("Relative operating table + carts (surgical light); supply/scrub on walls; monitor",
    "RoomGroup randomness=0.1", "operating table + surgical light retrieval", "HIGH — surgical equipment"),
"dental_office": ("Relative dental chair + stool + tray (exam light); cabinets; x-ray viewer",
    "RoomGroup randomness=0.12", "dental chair retrieval is the crux", "HIGH — dental chair"),
"library": ("Around reading table + chairs rectilinear (light); wall bookshelves; armchair corner",
    "Around jitter=0.4; RoomGroup randomness=0.15", "table+chairs jitter; bookshelf walls", "LOW"),
"restaurant": ("4× Around bistro tables (jitter, some lit); host stand; banquette",
    "Around jitter=0.5; RoomGroup randomness=0.25", "multiple table clusters spacing; banquette", "LOW"),
"computer_room": ("Grid workstation (desk+chair+monitor on top); server rack; whiteboard",
    "GridGroup randomness=0.3; RoomGroup randomness=0.2", "monitor-on-top; grid faces front", "MED — server rack"),
"tv_studio": ("Relative news desk (place_desk_chair) + presenters (light); Around camera arc; backdrop",
    "Around jitter=0.3; RoomGroup randomness=0.2", "news-desk pose; cameras-on-tripods retrieval", "HIGH — broadcast gear"),
"bookstore": ("Grid bookshelves; Pile book display (light); reading armchair; counter",
    "RoomGroup randomness=0.2", "book piles relax; shelves retrieval", "LOW"),
"hospital_room": ("Relative hospital bed + cabinet + IV (light); visitor chair; vitals monitor",
    "RoomGroup randomness=0.12", "hospital bed retrieval; IV stand", "HIGH — hospital bed/IV"),
"jewellery_shop": ("Around display counters rectilinear + stools (light); wall cabinet; mirror",
    "Around jitter=0.15; RoomGroup randomness=0.1", "glass cases retrieval; small luxe room", "HIGH — display cases"),
"deli": ("Relative deli counter (light); 2× Around cafe tables; product shelf; fridge; menu",
    "Around jitter=0.5; RoomGroup randomness=0.2", "deli counter + fridge retrieval", "MED — deli counter"),
"clothing_store": ("Grid clothing racks; Pile folded clothes (light); mannequins; counter; mirror",
    "GridGroup randomness=0.15; RoomGroup randomness=0.2", "racks + mannequins retrieval", "MED — retail apparel"),
"bakery": ("Relative pastry counter (light); 2× Around cafe tables; bread shelf; oven; menu",
    "Around jitter=0.5; RoomGroup randomness=0.2", "display counter + oven retrieval", "MED — bakery fixtures"),
"grocery_store": ("Grid gondola aisles; Pile produce; Grid checkout row; light_anchor cart; fridge case",
    "RoomGroup randomness=0.15", "gondola shelving + checkout retrieval", "HIGH — grocery fixtures"),
"fast_food": ("Grid booth units (table+benches); light_anchor; counter; drink station; menu",
    "GridGroup randomness=0.1; RoomGroup randomness=0.15", "booth bench seating; menu board mount", "MED — booth seating"),
"florist_shop": ("Around flower stands circle (heavy jitter, light); Pile flower buckets; counter",
    "Around jitter=0.6; RoomGroup randomness=0.25", "flower stands retrieval; lush feel", "HIGH — flower displays"),
"shoe_shop": ("Grid shoe-shelf rows on walls; Grid fitting-bench row; light_anchor stool; counter",
    "RoomGroup randomness=0.15", "shoe shelves retrieval; bench row", "MED — shoe display"),
"toy_store": ("Grid toy-shelf aisles; Pile plush (light); checkout; giant plush; signage",
    "RoomGroup randomness=0.2", "toy shelves + plush retrieval; color", "MED — toy retail"),
"buffet": ("Grid buffet counters row; 2× Around banquet tables (jitter, lit); beverage/plate stations",
    "Around jitter=0.5; RoomGroup randomness=0.25", "buffet counters retrieval; hall aspect", "HIGH — buffet fixtures"),
"greenhouse": ("Grid plant benches; Pile pots (light); corner tropicals; glass walls (2 windows)",
    "RoomGroup randomness=0.25", "plant benches retrieval; glass-wall feel", "MED — greenhouse benches"),
}


def main():
    os.makedirs(NOTES, exist_ok=True)
    for name, (pattern, rand, focus, gap) in DATA.items():
        body = (f"# {name.replace('_', ' ').title()}\n\n"
                f"- **Pattern:** {pattern}\n"
                f"- **Jitter/randomness:** {rand}\n"
                f"- **Review first:** {focus}\n"
                f"- **Asset-gap risk:** {gap}\n")
        with open(os.path.join(NOTES, name + ".md"), "w") as f:
            f.write(body)
    print(f"wrote {len(DATA)} notes to {NOTES}")


if __name__ == "__main__":
    main()
