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
| 1.13–3.67s | V1 |  | — |  |  |  |
| 3.67–5.17s | V2 |  | — |  |  |  |
| 3.67–19.48s | V6 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |  |
| 3.67–19.48s | V7 | ADJ | Lumetri Color |  |  |  |
| 3.67–34.49s | V8 |  | — |  |  |  |
| 3.67–5.17s | V9 |  | Text (Cream cheese) |  |  |  |
| 5.17–7.26s | V2 |  | Lumetri Color |  |  |  |
| 5.17–7.26s | V9 |  | Graphic Parameters | Room\rtemperature\rcream cheese is\rmuch easier to\rwork with! |  |  |
| 7.26–10.05s | V1 |  | — |  |  |  |
| 7.76–8.84s | V9 |  | Text (Scallion) |  |  |  |
| 8.84–10.05s | V9 |  | Text (Jalapeño pepper) |  |  |  |
| 9.88–10.18s | V2 | ADJ | Transform (Zoom In) [animated: Scale Height] |  |  |  |
| 10.05–10.18s | V1 |  | Mirror (Main), Mirror (Main), Mirror (Main), Mirror (Main), Replicate (Main), Lumetri Color |  |  |  |
| 10.05–11.51s | V9 |  | Text (Cranberries) |  |  |  |
| 10.18–11.51s | V1 |  | Lumetri Color |  |  |  |
| 11.51–12.85s | V1 |  | Lumetri Color |  |  |  |
| 11.51–12.85s | V9 |  | Text (Granulated sugar) |  |  |  |
| 12.85–14.18s | V1 |  | Lumetri Color |  |  |  |
| 12.85–14.18s | V9 |  | Text (Kosher salt) |  |  |  |
| 14.18–15.56s | V1 |  | Lumetri Color |  |  |  |
| 14.18–15.56s | V9 |  | Text (Lemon juice) |  |  |  |
| 15.56–17.02s | V1 |  | Lumetri Color |  |  |  |
| 17.02–18.52s | V2 |  | — |  |  |  |
| 18.52–19.48s | V1 |  | — |  |  | RAMP (6 keyframes) |
| 19.48–20.40s | V1 |  | — |  |  |  |
| 19.48–30.28s | V6 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |  |
| 19.48–30.28s | V7 | ADJ | Lumetri Color |  |  |  |
| 20.40–21.48s | V1 |  | — |  |  |  |
| 21.48–24.86s | V1 |  | — |  |  |  |
| 24.86–25.65s | V1 |  | — |  |  |  |
| 25.65–26.82s | V1 |  | — |  |  |  |
| 26.82–28.07s | V1 |  | Lumetri Color |  |  |  |
| 26.82–28.07s | V9 |  | Text (Fresh cilantro) |  |  |  |
| 28.07–30.28s | V1 |  | — |  |  |  |
| 30.28–31.53s | V1 |  | Lumetri Color |  |  |  |
| 30.28–37.54s | V6 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |  |
| 30.28–37.54s | V7 | ADJ | Lumetri Color |  |  |  |
| 31.53–32.66s | V1 |  | Lumetri Color |  |  |  |
| 32.66–34.49s | V1 |  | Lumetri Color, Mask2 (01), Lumetri Color |  | static 4-vertex mask |  |
| 34.49–37.54s | V1 |  | — |  |  |  |
| 34.70–37.54s | V8 |  | — |  |  |  |

**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**
- **3.67–19.48s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color (Green), Lumetri Color)
- **3.67–19.48s**: V6 (Lumetri Color (Green), Lumetri Color) stacked over V2 (Transform (Zoom In) [animated: Scale Height])
- **3.67–19.48s**: V7 (Lumetri Color) stacked over V2 (Transform (Zoom In) [animated: Scale Height])
- **19.48–30.28s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color (Green), Lumetri Color)
- **30.28–37.54s**: V7 (Lumetri Color) stacked over V6 (Lumetri Color (Green), Lumetri Color)

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=1.13s** — events: V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_2fps/frame_0003.jpg`

**t=3.67s** — events: V1 cut out; V2 cut in; V6 cut (adj) in; Lumetri Color(Green) starts; Lumetri Color starts; V7 cut (adj) in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0007.jpg`

**t=5.17s** — events: V2 cut out; V2 cut in; Lumetri Color starts; V9 cut out; Text(Cream cheese) ends; V9 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0025.jpg`

**t=7.26s** — events: V1 cut in; V2 cut out; Lumetri Color ends; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0050.jpg`

**t=7.76s** — events: V9 cut in; Text(Scallion) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0056.jpg`

**t=8.84s** — events: V9 cut out; Text(Scallion) ends; V9 cut in; Text(Jalapeño pepper) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0069.jpg`

**t=9.88s** — events: V2 cut (adj) in; Transform(Zoom In) starts; V1 cut out; V1 cut in; Mirror(Main) starts; Mirror(Main) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0082.jpg`

**t=11.51s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Text(Cranberries) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0101.jpg`

**t=12.85s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Text(Granulated sugar) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0117.jpg`

**t=14.18s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Text(Kosher salt) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0133.jpg`

**t=15.56s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Text(Lemon juice) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0150.jpg`

**t=17.02s** — events: V1 cut out; Lumetri Color ends; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0167.jpg`

**t=18.52s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0185.jpg`

**t=19.48s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color(Green) ends; Lumetri Color ends; V6 cut (adj) in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0197.jpg`

**t=20.40s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0208.jpg`

**t=21.48s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0221.jpg`

**t=24.86s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0261.jpg`

**t=25.65s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0271.jpg`

**t=26.82s** — events: V1 cut out; V1 cut in; Lumetri Color starts; V9 cut in; Text(Fresh cilantro) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0285.jpg`

**t=28.07s** — events: V1 cut out; Lumetri Color ends; V1 cut in; V9 cut out; Text(Fresh cilantro) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0300.jpg`

**t=30.28s** — events: V1 cut out; V1 cut in; Lumetri Color starts; V6 cut (adj) out; Lumetri Color(Green) ends; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0326.jpg`

**t=31.53s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0341.jpg`

**t=32.66s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; Mask2(01) starts; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0355.jpg`

**t=34.49s** — events: V1 cut out; Lumetri Color ends; Mask2(01) ends; Lumetri Color ends; V1 cut in; V8 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0377.jpg`

**t=37.54s** — events: V1 cut out; V6 cut (adj) out; Lumetri Color(Green) ends; Lumetri Color ends; V7 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cranberry_jalepeno_dip_frames_12fps/frame_0411.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
