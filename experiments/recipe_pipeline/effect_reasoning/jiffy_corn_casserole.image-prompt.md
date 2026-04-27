# Effect Reasoning Prompt — Recipe Edit Analysis

You are analyzing a Premiere Pro edit of a Kitchn recipe video that Dan de Jesus cut. Your job is to reason about *why* he made each editorial decision — not to assign decisions to a pre-existing taxonomy. We want your fresh observations so we can later cluster recurring intents into vocabulary.

## What you have

Three inputs, in this order:

1. **`PRPROJ_EFFECTS`** — a compact list of every editorial event in the timeline: cuts (clip in/out per track), adjustment-layer effects (Transform, Lumetri, Mirror, Replicate, Mask), per-clip Lumetri grades, MOGRT text overlays, masks, and stacked-adjustment-layer composites. Times are in timeline seconds.

2. **`FRAME_ANALYSIS`** — a per-frame visual description of the rendered video at 2fps. Each row tells you which camera angle is on screen (FRONT, OVERHEAD, etc.), what's happening (subject, action, hands, ingredients), and any overlay text.

3. **`EXISTING_ANNOTATION`** — Dan-validated editorial reasoning that's already been done on this recipe at the cut/beat/rhythm level. Treat this as ground truth for the structural analysis. Your job adds the *why-this-effect-here* layer.

## What we want from you

For each meaningful editorial choice in the edit — every cut, every effect, every angle change — explain what's happening and offer a hypothesis about why Dan might have made that choice. Pay specific attention to:

- **Where cuts land relative to the action.** Does the cut come on a beat (visible action peak), before the action (anticipation), after (reaction), or in the middle (compression)?
- **Why one angle transitions to another.** What does FRONT show that OVERHEAD doesn't? When Dan moves OVERHEAD → FRONT or vice versa, what's the editorial reason?
- **Each effect's contribution.** A Transform punch-in adds what the underlying clip lacks — what specifically? A Lumetri grade does what to the mood? A Mirror+Replicate kaleidoscope marks what kind of moment?
- **Stacked composites.** When two or more adjustment layers overlap (e.g., a Zoom Transform on V5 atop a Mirror+Replicate on V3), what makes that combination the right answer rather than either effect alone?
- **Hand-presence vs hand-absence.** When the frame analysis says "no hands in frame" or describes the ingredient/object simply *appearing* (vs. a hand pouring/dropping/manipulating), that's a deliberate **stop-motion / found-object** beat with a different vibe than a hand-action shot. Pairs of consecutive overhead beats where one shows action and the next shows no hands are common — call this out specifically; it is one of Dan's signature mood shifts.
- **Absence of an adjustment-layer effect ≠ static / locked-off.** Before describing a section as "still" or "static-feeling" because no Transform/effect is applied, READ THE FRAME ANALYSIS for in-shot action (steak flipping, sizzling, hand entering frame, smoke rising, motion blur, etc.). If the underlying shot is already kinetic — the cooking sizzle, a hand placing a hero, a slicing motion — that's why no effect was needed. The shot is doing the motion work. Only call something static when the frames themselves describe a held/locked composition with minimal change.
- **What the alternative would have been.** If Dan hadn't done this — straight cut instead of zoom, FRONT instead of OVERHEAD, no kaleidoscope — what would have been lost?

## What we don't want

- **Don't assign tags from a fixed vocabulary.** No "energy bump" / "sectional emphasis" labels. Use natural language — explain in your own words what's happening editorially.
- **Don't moralize or grade the edit.** No "this is a great cut" / "this could be tighter." We want analysis, not critique.
- **Don't restate the structural analysis from EXISTING_ANNOTATION.** That layer is done. Add the effect-and-angle layer on top.
- **Don't speculate about ingredients or recipe content.** Stay editorial.

## Output format

**Be terse.** Bullets, not paragraphs. No flowing analysis prose. Reader should be able to scan a section in 5 seconds. Cut every "this is interesting because" / "notably" / "what's happening here is" — just state the thing.

Markdown. Walk the edit roughly in timeline order. Group observations by editorial moment (a cluster of cuts/effects that belong together — e.g., "marinade build" or "onion-toss accent"). For each moment, use this exact structure — one short bullet per field, no paragraphs:

```
### {timeline range} — {short descriptive title}

- **Screen:** {one short line — angle + key action; flag "no hands" / stop-motion appearance if relevant}
- **Cuts/angles:** {one line on cut count, angle sequence, rhythm}
- **Effects:** {what's active, with key params}
- **Why:** {one short bullet — the editorial logic, not flowing prose}
- **Without:** {what the alternative would lose, in 1–2 short clauses}
```

If a section is uneventful, collapse it to one or two bullets — don't pad.

End with an **OBSERVATIONS** section — 5–10 bullet points listing patterns that recur or seem like Dan's signatures. Each bullet 1–2 sentences max. These will be the input to vocabulary-clustering across recipes, so be specific (not "uses zooms" but "uses slow Position+Scale on adjustment layers over multi-clip ingredient-dump sections to add motion energy without recutting").

## Inputs follow

---

### PRPROJ_EFFECTS

**Timeline (cuts + effects + masks + MOGRT text + speed, ordered by in-time):**

| Timeline | Track | Adj | Effects | Text overlay | Mask | Speed |
|---|---|---|---|---|---|---|
| 1.17–2.42s | V1 |  | — |  |  |  |
| 1.17–2.42s | V6 | ADJ | Lumetri Color, Mask2 (01) [animated: Path, Position, Anchor Point], Lumetri Color |  | static 12-vertex mask |  |
| 2.42–3.80s | V1 |  | — |  |  |  |
| 2.42–3.80s | V6 | ADJ | Lumetri Color, Mask2 (01) [animated: Path, Position, Anchor Point], Lumetri Color |  | static 11-vertex mask |  |
| 3.80–5.13s | V1 |  | Lumetri Color, Mask2 (01) |  | static 7-vertex mask |  |
| 3.80–5.13s | V6 | ADJ | Lumetri Color |  |  |  |
| 3.80–22.77s | V8 |  | — |  |  |  |
| 3.80–5.13s | V9 |  | Text (Unsalted butter) |  |  |  |
| 5.13–7.84s | V1 |  | — |  |  |  |
| 5.13–7.84s | V6 | ADJ | Lumetri Color |  |  |  |
| 5.13–7.84s | V9 |  | Graphic Parameters | Microwave until melted |  |  |
| 7.84–9.22s | V1 |  | Lumetri Color, Mask2 (01) |  |  |  |
| 7.84–9.22s | V6 | ADJ | Lumetri Color |  |  |  |
| 7.84–9.22s | V9 |  | Text (Sour cream) |  |  |  |
| 9.22–14.35s | V1 |  | — |  |  |  |
| 9.22–14.35s | V6 | ADJ | Lumetri Color |  |  |  |
| 9.84–11.43s | V9 |  | Text (Eggs) |  |  |  |
| 14.35–16.06s | V1 |  | Lumetri Color, Mask2 (01) |  | static 7-vertex mask |  |
| 14.35–16.06s | V6 | ADJ | Lumetri Color, Lumetri Color |  |  |  |
| 14.35–16.06s | V9 |  | Lumetri Color, Mask2 (01), Text (Corn kernels & creamed corn) |  |  |  |
| 16.06–17.18s | V1 |  | — |  |  |  |
| 16.06–18.52s | V6 | ADJ | Lumetri Color |  |  |  |
| 17.18–18.52s | V1 |  | — |  |  |  |
| 18.52–20.60s | V1 |  | — |  |  |  |
| 18.52–20.60s | V6 | ADJ | Lumetri Color |  |  |  |
| 20.60–22.61s | V1 |  | — |  |  |  |
| 20.60–22.61s | V6 | ADJ | Lumetri Color |  |  |  |
| 20.60–22.61s | V9 |  | Text (Jiffy corn muffin mix) |  |  |  |
| 22.61–24.36s | V1 |  | — |  |  |  |
| 22.69–24.36s | V6 | ADJ | Lumetri Color |  |  |  |
| 22.77–42.58s | V7 | ADJ | Lumetri Color |  |  |  |
| 22.77–38.12s | V8 |  | — |  |  |  |
| 24.36–25.73s | V1 |  | — |  |  |  |
| 24.36–27.78s | V6 | ADJ | Lumetri Color |  |  |  |
| 25.73–27.78s | V1 |  | — |  |  |  |
| 27.78–34.74s | V1 |  | — |  |  |  |
| 27.78–34.74s | V6 | ADJ | Lumetri Color |  |  |  |
| 32.49–34.74s | V9 |  | Graphic Parameters | Bake at 350°F until puffed and browned,\r45 to 50 minutes |  |  |
| 34.74–36.87s | V1 |  | — |  |  |  |
| 34.74–36.87s | V6 | ADJ | Lumetri Color |  |  |  |
| 36.87–38.12s | V1 |  | — |  |  |  |
| 36.87–38.12s | V6 | ADJ | Lumetri Color |  |  |  |
| 38.12–42.58s | V1 |  | — |  |  |  |
| 38.12–42.58s | V6 | ADJ | Lumetri Color, Mask2 (02) [animated: Path, Position, Anchor Point], Lumetri Color |  | static 9-vertex mask |  |
| 39.87–42.58s | V8 |  | — |  |  |  |

**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**
- **22.69–42.58s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color)
- **22.77–42.58s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color)
- **22.77–42.58s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color)
- **22.77–42.58s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color)
- **22.77–42.58s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color)
- **22.77–42.58s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color, Mask2 (02) [animated: Path, Position, Anchor Point], Lumetri Color)

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=1.17s** — events: V1 cut in; V6 cut (adj) in; Lumetri Color starts; Mask2(01) starts; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0007.jpg`

**t=2.42s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; Mask2(01) ends; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0022.jpg`

**t=3.80s** — events: V1 cut out; V1 cut in; Lumetri Color starts; Mask2(01) starts; V6 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0039.jpg`

**t=5.13s** — events: V1 cut out; Lumetri Color ends; Mask2(01) ends; V1 cut in; V6 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0055.jpg`

**t=7.84s** — events: V1 cut out; V1 cut in; Lumetri Color starts; Mask2(01) starts; V6 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0087.jpg`

**t=9.22s** — events: V1 cut out; Lumetri Color ends; Mask2(01) ends; V1 cut in; V6 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0104.jpg`

**t=9.84s** — events: V9 cut in; Text(Eggs) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0111.jpg`

**t=11.43s** — events: V9 cut out; Text(Eggs) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0130.jpg`

**t=14.35s** — events: V1 cut out; V1 cut in; Lumetri Color starts; Mask2(01) starts; V6 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0165.jpg`

**t=16.06s** — events: V1 cut out; Lumetri Color ends; Mask2(01) ends; V1 cut in; V6 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0186.jpg`

**t=17.18s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0191.jpg`

**t=18.52s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_2fps/frame_0038.jpg`

**t=20.60s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0198.jpg`

**t=22.61s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V9 cut out; Text(Jiffy corn muffin mix) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0222.jpg`

**t=24.36s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0243.jpg`

**t=25.73s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0260.jpg`

**t=27.78s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0284.jpg`

**t=32.49s** — events: V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0341.jpg`

**t=34.74s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0368.jpg`

**t=36.87s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0393.jpg`

**t=38.12s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0408.jpg`

**t=39.87s** — events: V8 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0429.jpg`

**t=42.58s** — events: V1 cut out; V6 cut (adj) out; Lumetri Color ends; Mask2(02) ends; Lumetri Color ends; V7 cut (adj) out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/jiffy_corn_casserole_frames_12fps/frame_0462.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
