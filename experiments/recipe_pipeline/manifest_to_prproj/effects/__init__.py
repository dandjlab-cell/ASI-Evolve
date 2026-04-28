"""Per-intent effect emitters.

Each module in this package emits one editorial-intent's XML payload (Motion,
Lumetri, Mask2, Mirror+Replicate, TimeRemapping, MOGRT text — see Decision 3
in Brain/Projects/RoughCut/Architecture — Lessons from Claude Code Paper.md
for the full target list).

Round 1 ships only motion.py (per-clip Motion.Scale override for source/sequence
resolution mismatch). Round 2-3 adds the rest.

Effect emitters depend on core/ (ClassIDs, IdFactory, tick_math). The reverse
direction is forbidden — core stays bucket-agnostic and effect-agnostic.

Future addition: a registry that dispatches by editorial-intent tag in the
manifest, so a beat tagged `slow-mo-hero-pour` calls into `time_remapping.py`,
`chapter-break-kaleidoscope` calls `mirror_replicate.py + transform.py`, etc.
The registry is intentionally not built yet — wait until 2-3 emitters exist
to see the right shape.
"""
