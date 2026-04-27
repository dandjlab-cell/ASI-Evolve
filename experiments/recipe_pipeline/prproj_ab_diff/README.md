# prproj A/B diff harness

For decoding `ArbVideoComponentParam` blobs (Lumetri Color, Essential Graphics text, Mask2 vertices, etc.) using the established reverse-engineering method.

## Recipe

1. **Open Premiere.** Create a minimal project with one video clip on V1.
2. **Apply the effect under investigation** at a known-default state. Save as `project_a.prproj`.
3. **Save As** → `project_b.prproj`. Change ONE attribute (e.g. Saturation 0 → 50). Save.
4. Run:
   ```bash
   python diff_arb_payloads.py project_a.prproj project_b.prproj --match-name "AE.ADBE Lumetri"
   ```
5. The script reports byte-level diffs in any matching `ArbVideoComponentParam` payload. Hex + UTF-16 views to help you spot the encoding (numeric, string, struct).
6. Iterate: vary one attribute at a time. After 5–10 diffs you'll have the byte-offset map for the effect.
7. Capture findings in `Brain/Knowledge/API Integration/Premiere {Effect Name} via prproj.md`.

## Tasks waiting on this

- **Lumetri Color** (`AE.ADBE Lumetri`) — A/B test ideas: Saturation, Vibrance, Exposure, Contrast, Temperature, individual creative LUT slot. Each diff isolates one numeric field.
- **Essential Graphics text** (`AE.ADBE Capsule`) — A/B test idea: change text content of a single text layer in a MOGRT instance. The UTF-16 view in the diff will show the new string verbatim if it's stored as plain text.
- **Mask2 shape** (`AE.ADBE AEMask2`) — A/B test idea: drag one vertex of a mask shape ~10 px. Diff shows the vertex coord encoding.

## When the harness reports zero diffs

- Confirm the change actually persisted (close+reopen the project before saving as B).
- Try without `--match-name` — the attribute may live in a different effect's payload.
- Some Premiere settings live outside `ArbVideoComponentParam` (e.g. project-level color management). Grep the decompressed XML directly for the attribute name.

## See also

- `Brain/Knowledge/API Integration/Premiere prproj Reverse Engineering Method.md` — the canonical method
- `Brain/Knowledge/API Integration/Premiere Mask2 via prproj.md` — example of a partial decode (presence + structure done; vertex blob still pending the diff harness)
