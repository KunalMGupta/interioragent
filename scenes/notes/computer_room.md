# Computer Room

- **Status:** BUILT & converged (`scenes/computer_room.py`, seed=11) — see `skills/examples/computer_room.md`.
- **Pattern:** reusable `WorkstationGroup` station (desk + chair + `place_computer` + pen-cup
  accessory) → GridGroup rows (2×4) facing the front wall; front wall = large display + whiteboard
  + door; server rack + equipment shelf on the back wall; window/blinds on a long wall.
- **Build ONCE, `8 * ws`:** one `place_on_top` tournament → 8 identical stations.
- **Key fixes:** WorkstationGroup operator side is +Z → `face(stations, toward="back_wall")` to point
  users at the FRONT display (opposite of place_desk_chair; verify seating dir in the render). Plain
  color+material texture strings ("smooth cool grey concrete floor", not "anti-static vinyl").
- **Jitter/randomness:** GridGroup randomness=0.3; RoomGroup modulate_scale=1.0, randomness=0.18.
- **Assets:** **server rack INGESTED** (`custom/9f2a77c7…` from server_racking_system.glb, pinned as
  `_RACK`) — base dataset had no true rack. Teal desk privacy screen (plan accent) deliberately dropped.
