# Dental Office

- **Pattern:** Compact single **operatory** (near-square, not wide). Central dental-unit group
  (chair+light+delivery+monitor+cuspidor) + saddle stool + assistant cart; wood sink vanity +
  tall supply cabinet on side walls; botanical accent + kids poster; LED ceiling panels.
- **Hero = ONE ingested UNIT** (`custom/64a7f627…`, pinned): a complete dental unit mesh closes
  the chair/light/delivery/monitor gaps at once. Dataset has NO true dental chair — kickoff must
  source+ingest one. See `skills/examples/dental_office.md`.
- **Jitter/randomness:** RoomGroup randomness=0.12, modulate_scale=0.85 (acts on room-rescale VLM).
- **Gotchas:** `place_rug` returns ornate rugs (drop the rug, clinical hard floor); green accent
  via a back-wall botanical print (no per-wall texture API); `place_window_picture` is wide and
  collides with a same-wall door → use `place_window_standard(position=...)`.
- **Asset-gap risk:** SOLVED for the chair (ingested). Substitutes: vanity-set = sink counter.
- **Status:** built end-to-end 2026-07-05; all VLM feedback clean (no rescale/rotation/overlap).
