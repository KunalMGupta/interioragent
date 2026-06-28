# hair_salon — .glb ingestion spec sheet

You're supplying these as `.glb` files. The ingest tool does NOT re-orient or re-scale meshes,
so each glb must already be:

- **Y up**, **front facing +Z**, **width along X**, in **real-world metres**.
- One object per file. Name the files exactly as the `file` column below (the prepared
  `hair_salon_manifest.json` is keyed to these names, so scale/placement/description are fixed
  and not left to a VLM guess).

Hand-off: drop the glbs into a folder, `zip` them, tell me the path. I run:
`python -m IDSDL.ingest <zip> --category hair_salon --manifest scenes/work/hair_salon_manifest.json`
Then I render-verify each (front preview + caption + scale) before we freeze the pool.

## Required (the dataset genuinely lacks these)

| file | object | orientation (faces +Z) | real width | notes |
|---|---|---|---|---|
| `barber_chair.glb` | Salon **barber/styling chair** | seat opening / person faces +Z | **0.65 m** | upholstered seat+back+arms on ONE chrome **hydraulic pedestal** + round base + chrome footrest ring. ~0.95 m deep, ~1.1 m tall. |
| `backwash_unit.glb` | **Backwash / shampoo unit** | client reclines toward +Z, **basin at back (−Z)** | **0.75 m** | reclining chair joined to a ceramic **neck-rest wash bowl** behind the headrest; chrome tap/hose. ~1.3 m deep, ~1.0 m tall. Usually set against a wall (basin to wall). |
| `hood_dryer.glb` | Standing **hood / bonnet dryer** | seat faces +Z, hood over head | **0.60 m** | chair or pedestal with a large **dome hood**; chrome stem + weighted base; controls on hood. ~0.7 m deep, ~1.5 m tall. |

## Optional (softer, cross-category — casino needs neon too)

| file | object | orientation | real width | notes |
|---|---|---|---|---|
| `salon_neon_sign.glb` | **Neon salon wall sign** | visible face +Z, thin in Z | **1.10 m** | emissive neon-tube lettering ("SALON"/"HAIR") on a dark backing; wall-mounted; ~0.45 m tall, ~0.05 m deep. |
| `salon_menu_board.glb` | Wall **price / services board** | face +Z, thin in Z | **0.80 m** | framed board listing services/prices; wall-mounted; ~1.1 m tall. |

## Verify-after-ingest checklist (I'll do this)
- preview renders head-on, not edge-on (confirms front = +Z);
- caption names the right object; `placement` = floor (chairs/units/dryer) or wall (signs);
- `scale` matches the width above (manifest pins it, so this should be exact);
- a quick `AddAsset("<query>")` retrieves the new asset for its intended slot.
