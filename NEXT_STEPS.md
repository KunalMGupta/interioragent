# NEXT STEPS (session handoff — delete when drained)

Queue agreed with Kunal 2026-07-14. Item 1 is IN PROGRESS; 2–4 are queued behind it
(compact context before starting 2).

## 1. Kitchen island/dining rework (NEARLY DONE)
DONE: `KitchenIslandGroup` implemented (groups_extra.py + scene.py factory; surface-sampled
footprint raster, tip/pocket/front modes, entry-gap + stool-fit guards, analysis exposed);
tests 52–53 PASS; docs figure added; SKILL.md third precedent written; kitchen.md island
rules + camera-bound refinement written; examples README row updated; **kitchen_set_v3 (U)
DONE** — full build converged clean, promoted to skills/examples.
REMAINING: kitchen_l_v1 build 5 running (set 2.1 m, shell 0.95 — builds 3/4 hit the
tall-inner-column camera bound, now sized per run <= W/2 - 0.3); on pass: promote program,
append the L worked section to kitchen.md, commit + push.

## 2. Scene batches for the six user-facing categories + feedback loop
living room, dining room, bedroom, kitchen, bathroom, study room — Kunal expects users to
test these heavily. 3–4 DIVERSE scenes per category (vary layout pattern / palette / brief,
not just seeds). Can run builds in parallel. Then a REVIEW MECHANISM: something Kunal can go
through scene by scene and leave feedback on (e.g. a review manifest MD/HTML gallery with
per-scene slots for verdict + notes), which we then act on and fold into lessons.

## 3. Room height must auto-fix at compile
There should NEVER be an asset poking through the roof. `RoomGroup` should adjust room
height at compile time (today: HEIGHT hard-clamped to 3.0 — `min(max(heights+2,3),3)` — and
tall assets clip). Design: raise ceiling to tallest non-light child + margin, or auto-shrink
the offender; check camera-height interactions (`renderer/utils.py` eye = 0.55*H).

## 4. Constraints-compilation lesson
An exhaustive reference lesson: which constraints to impose for which asset categories /
situations (e.g. reception desk ⇒ front+side clearance; appliance ⇒ CategoryClearance;
door ⇒ auto clearance; tall fixture ⇒ off wall-centres…). Method: run several examples,
curate the list, then DISCUSS THE LIST WITH KUNAL thoroughly before promoting it as the
reference (skills/workflow/constraints.md).
