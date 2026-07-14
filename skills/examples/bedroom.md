# Bedroom — worked example ("Warm Traditional Master Suite")

Status: **built & VLM-clean** as `scenes/work/bedroom.py` (seed=41), planner-driven, iterated on VLM
feedback. [`bedroom_v1.py`](bedroom_v1.py) is that program **phase-gated** (2026-07-13):
`lint_program`-clean, and **phase 1 rebuilt and verified** — `no rotation`, `no wall overlap`, the
layout reproduces, and the surface/wall layers correctly stay out of the phase-1 render.
**Phases 2 and 3 have not been re-run since the retrofit.**

The phase-1 build votes `rescale room by 1.4`. **Not actioned** — see
[Lesson 5](#lesson-5--a-room-size-vote-on-a-phase-1-room-is-voting-on-a-room-that-does-not-exist-yet).

## Prompt(s) this covers
- "a warm, traditional master bedroom: a big bed with a substantial headboard, matching nightstands
  and lamps, a bench at the foot, a wood dresser with a mirror, and a cozy reading corner."

## Plan summary (from the planner)
"Warm Traditional Master Suite." The bed is the central focal anchor on the main wall, with
**symmetry** as the organising idea — identical nightstands and lamps flanking a substantial
headboard. A storage bench at the foot, a classic wood dresser with a framed mirror, an armchair
reading nook. A large patterned rug grounds the sleep zone; floor-length curtains; layered warm
lighting. Palette: creams, taupes, soft golds, rich warm wood, muted-burgundy accents.

## The layout idea: SYMMETRIC HERO + a self-contained NOOK

**The core residential pattern**, and the one `hospital_room` later inherits wholesale (hero bed +
purpose-loaded walls). One hero owns the main wall; every other wall gets exactly one job; the
centre stays open.

| Wall | Job |
|---|---|
| back | the bed **hero** — nightstands, foot bench, and the nook hanging off its right flank |
| left | the dresser (styled), with a mirror above it |
| right | the window — **the only wall with no furniture**, so it stays the light source |
| front | the door (left) + a corner plant to fill the dead corner |
| centre | deliberately **open**; the rug does the grounding |

The subtlety that makes it read: the nightstands are placed relative to the **headboard**
(`place_on_back_left` / `place_on_back_right`), *not* the bed's left and right. Place them on the
bed's sides and they slide down toward the foot, and the symmetry — the entire point of the plan —
quietly dies.

## Pinned assets (audited previews)

| Role | id | Why pinned |
|---|---|---|
| bed | `hssd/298cd407…` | a **SET asset** — ships fully dressed |
| nightstand | `hssd/830e2ed4…` | |
| bench | `hssd/448a7a6a…` | |
| dresser | `hssd/d913eb66…` | |
| table lamp | `hssd/d0fcbd96…` | the generic query kept returning **modern white** lamps |
| floor lamp | `hssd/9c9f2473…` | |
| landscape art | `hssd/4192b936…` | the retrieved painting was a **bad mesh** |

## Asset gaps
None blocking. Everything the plan asked for exists in the pool; the two pins above are *style*
corrections, not gap workarounds.

## Lesson 1 — beds are SET assets: the mesh comes fully dressed
Pin a good traditional bed and **do not** add bedding or pillows. The asset already carries them and
a `place_on_top` pillow fights the mesh. Same family as vanities, toilets and fitted kitchen sets
(see [`kitchen.md`](kitchen.md), which is the extreme version of this rule). Beds also carry
real-world scale, so no height override is needed — a rare asset class where you can trust the mesh.

## Lesson 2 — build ONE symmetric unit, then duplicate it with `2 * unit`
The matching nightstand+lamp pair is built **once** as a `RelativeGroup` and then duplicated:

```python
with scene.RelativeGroup() as ns:
    ns.set_anchor(nightstand)
    if PHASE >= 2:
        ns.place_on_top(lamp)
ns_l, ns_r = 2 * ns
```

Build the two separately and `place_on_top`'s sizing tournament runs **twice** — so the two lamps
come out **different sizes**, on a pair whose entire job is to be identical. One unit → one
tournament → a true pair. This is the general "build a repeated unit once, then copy it" principle
that `classroom` and `computer_room` scale up into grids.

## Lesson 3 — pre-scale wall art BEFORE `place_on_wall_*`, or it punches through the ceiling
`place_on_wall_*` derives the mount height from the art's **un-scaled** height. A large painting is
therefore mounted too high and clips the ceiling. Scale it down *first*:

```python
art.scale_only_width(1.1); art.scale_only_height(0.75); art.scale_only_depth(0.04)
room.place_on_wall_back_center(art)
```

## Lesson 4 — a seat never travels alone
The reading chair carries its side table and its floor lamp **inside its own group**, so the lamp is
not stranded in a corner and all three rotate together when the nook is angled. Then
`bed_group.face(chair_group, toward=bench)` — **`face()` works on a nested group, not just a leaf**,
which is what lets the whole nook pivot toward the bed as one piece.

This is also the rule `living_room_cozy` v3 had to relearn the hard way: because `place_on_top`
seats items on the group's **anchor**, a lamp meant for a side table must be anchored on the *table*,
not dropped into a group anchored on the chair — or it lands on the cushion.

## Lesson 5 — a room-size vote on a phase-1 room is voting on a room that does not exist yet
Minted by the phase-gating retrofit (2026-07-13), and the reason this example is worth re-reading.

The **same program** converged **VLM-clean at `modulate_scale=0.8`** on the full build. Rebuilt at
**phase 1**, it votes `rescale room by 1.4` — grow the room by 40%. Same layout, same seed, opposite
verdict. Nothing about the floor plan changed; the only difference is that the rug, the lamps, the
plant and the art are not there yet.

Act on that vote and you would inflate the shell by 40%, then watch phases 2 and 3 fill it — and end
up with the cavernous hotel-lobby bedroom the `modulate_scale=0.8` was there to prevent.

**Rule: room-size votes are only meaningful on a FULL build.** During phase 1 and 2 they are voting
on a deliberately half-dressed room, so read them for layout signal (`no rotation`, `no wall
overlap`, `no rescale` on individual objects) and ignore the shell verdict entirely. This is the
phase-aware sharpening of `kitchen`'s rule — *the occupancy vote tells you THAT the room is wrong,
never WHICH slot did it* — and it explains why `laundromat`'s sparse room could legitimately shrink
below 1.0 while this one appears to want to grow.

*Caveat, honestly:* phases 2 and 3 have not been re-run since the retrofit, so this reads the
phase-1 vote against the **original** converged full build rather than a fresh one. The conclusion
holds either way — the two verdicts cannot both be right.

## Program
[`bedroom_v1.py`](bedroom_v1.py) — phase 1 the floor anchors (bed hero, nightstands, bench, nook,
dresser, walls, door), phase 2 the surface dressing (lamps, dresser top, rug, plant), phase 3 the
wall decor, window and ceiling light.

`workbench run skills/examples/bedroom_v1.py --phase 1` builds the layout alone in ~1–2 min.

Note the door is **ungated** — it runs in phase 1 because its automatic clearance shapes the floor
solve, so deferring it would change the layout you validated.

## What worked / gotchas
- `modulate_scale=0.8` on the `RoomGroup`. A master bedroom that solves to a full-size shell reads
  like a hotel lobby; the room must feel intimate. This is the residential counterpart to
  `laundromat`'s "a genuinely sparse room may shrink below 1.0."
- Warm oak floor + greige walls: warmth that does not blow out under daylight.
- The right wall is kept furniture-free on purpose. It is the window wall, and a bedroom that loses
  its light source to a wardrobe stops reading as restful.

## VLM feedback we hit and how we resolved it
**Not recorded.** This scene predates the convention of logging the loop, and the build's feedback
history was never written down — the traps in Lessons 1–4 survive only because they were caught in
the program's comments. That is a real gap: if you rebuild this scene, log the votes.

## Manual constraints used
None beyond the defaults. Door clearance comes free from `CategoryClearanceConstraint`; the bed's
own footprint does the rest.

## Possible refinements (not blocking)
- **Re-run phases 2 and 3** on the gated program. Phase 1 is verified; the other two are not, and
  Lesson 5's caveat closes only when someone does.
- The muted-burgundy accent the planner asked for never landed — see `classroom`'s rule ("an accent
  colour the texture library lacks: drop it, don't smuggle it into the wall string"). Textiles are
  the escape hatch (`music_studio`), and a burgundy throw or rug would carry it honestly.
