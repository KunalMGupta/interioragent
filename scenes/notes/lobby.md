# Lobby

- **Pattern:** Single room, zoned — reception anchor (back third) + symmetric waiting lounge (centre).
  `RelativeGroup` reception (desk + chair behind + computer/plant on top); `AroundGroup.place_rectilinear`
  lounge (2 sofas + 2 armchairs around a coffee table, auto-faced inward) on a rug; plants, art, glazing.
- **Hero:** ingested wood+marble reception desk `custom/cffded…` (user supplied 3; dataset had 1 wooden).
- **Reception facing:** `place_on_back` (NOT `place_on_back_wall`) so staff have space; orient the on-top
  computer + chair at ROOM level (`room.face(chair, "front_wall")` / `room.face(computer, "back_wall")`).
- **Lighting:** flush DISC + `modulate_scale=2.2` + `density=0.03` → ~9 fixtures (a small fixture at 0.2 = ~250 dots).
- **Windows:** floor-to-ceiling with `curtain=None` (curtain meshes render as ghost drapes over the night void).
- **Built & VLM-clean** (seed=13); full write-up in `skills/examples/lobby.md`. Asset-gap risk: LOW (reception desk ingested).
