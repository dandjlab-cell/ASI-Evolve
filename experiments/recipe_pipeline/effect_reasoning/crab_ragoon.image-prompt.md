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
| 1.63–3.34s | V1 |  | Lumetri Color |  |  |  |
| 3.34–4.75s | V2 |  | — |  |  |  |
| 3.34–43.71s | V6 | ADJ | Lumetri Color |  |  |  |
| 3.34–39.66s | V7 |  | — |  |  |  |
| 3.34–4.75s | V8 |  | Text (Cream cheese) |  |  |  |
| 4.75–6.17s | V1 |  | — |  |  |  |
| 4.75–6.17s | V8 |  | Text (Imitation crab) |  |  |  |
| 6.17–7.34s | V1 |  | — |  |  |  |
| 6.17–7.34s | V8 |  | Text (Garlic) |  |  |  |
| 7.34–8.47s | V2 |  | — |  |  |  |
| 7.34–8.47s | V8 |  | Text (Scallions) |  |  |  |
| 8.47–9.59s | V1 |  | — |  |  |  |
| 8.47–9.59s | V8 |  | Text (Soy sauce) |  |  |  |
| 9.59–10.72s | V1 |  | — |  |  |  |
| 9.59–10.72s | V8 |  | Text (Granulated sugar) |  |  |  |
| 10.72–11.89s | V1 |  | — |  |  |  |
| 10.72–11.89s | V8 |  | Text (Toasted sesame oil) |  |  |  |
| 11.89–13.05s | V1 |  | — |  |  |  |
| 11.89–13.05s | V8 |  | Text (Garlic powder) |  |  |  |
| 13.05–14.31s | V1 |  | — |  |  |  |
| 13.05–14.31s | V8 |  | Text (Ground white pepper) |  |  |  |
| 14.31–16.18s | V2 |  | — |  |  |  |
| 16.18–17.85s | V1 |  | — |  |  |  |
| 17.85–20.31s | V2 |  | — |  |  |  |
| 17.85–19.27s | V8 |  | Text (Wonton wrappers) |  |  |  |
| 19.27–20.31s | V8 |  | Text (Crab mixture) |  |  |  |
| 20.31–21.48s | V1 |  | — |  |  |  |
| 20.31–23.57s | V8 |  | Graphic Parameters | Trace the border with\ra finger dipped in water |  |  |
| 21.48–22.31s | V1 |  | — |  |  |  |
| 22.31–23.57s | V1 |  | — |  |  |  |
| 23.57–24.69s | V1 |  | — |  |  |  |
| 24.69–26.32s | V1 |  | — |  |  |  |
| 26.32–27.36s | V1 |  | — |  |  |  |
| 27.36–28.74s | V1 |  | — |  |  |  |
| 28.74–30.07s | V2 |  | — |  |  |  |
| 30.07–31.53s | V1 |  | Lumetri Color |  |  |  |
| 31.53–32.62s | V2 |  | Lumetri Color |  |  |  |
| 32.62–33.83s | V1 |  | Lumetri Color |  |  |  |
| 33.83–35.41s | V1 |  | Lumetri Color |  |  |  |
| 33.83–35.41s | V8 |  | Text (Kosher salt) |  |  |  |
| 35.41–37.00s | V1 |  | Lumetri Color |  |  |  |
| 37.00–38.29s | V1 |  | Lumetri Color |  |  |  |
| 38.29–39.66s | V2 |  | — |  |  |  |
| 39.66–43.71s | V1 |  | — |  |  |  |
| 39.83–43.71s | V7 |  | — |  |  |  |

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=1.63s** — events: V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0004.jpg`

**t=3.34s** — events: V1 cut out; Lumetri Color ends; V2 cut in; V6 cut (adj) in; Lumetri Color starts; V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0007.jpg`

**t=4.75s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Cream cheese) ends; V8 cut in; Text(Imitation crab) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0024.jpg`

**t=6.17s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Imitation crab) ends; V8 cut in; Text(Garlic) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0013.jpg`

**t=7.34s** — events: V1 cut out; V2 cut in; V8 cut out; Text(Garlic) ends; V8 cut in; Text(Scallions) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0016.jpg`

**t=8.47s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Scallions) ends; V8 cut in; Text(Soy sauce) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0018.jpg`

**t=9.59s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Soy sauce) ends; V8 cut in; Text(Granulated sugar) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0020.jpg`

**t=10.72s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Granulated sugar) ends; V8 cut in; Text(Toasted sesame oil) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0022.jpg`

**t=11.89s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Toasted sesame oil) ends; V8 cut in; Text(Garlic powder) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0025.jpg`

**t=13.05s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Garlic powder) ends; V8 cut in; Text(Ground white pepper) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0027.jpg`

**t=14.31s** — events: V1 cut out; V2 cut in; V8 cut out; Text(Ground white pepper) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0031.jpg`

**t=16.18s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0054.jpg`

**t=17.85s** — events: V1 cut out; V2 cut in; V8 cut in; Text(Wonton wrappers) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0066.jpg`

**t=19.27s** — events: V8 cut out; Text(Wonton wrappers) ends; V8 cut in; Text(Crab mixture) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0083.jpg`

**t=20.31s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Crab mixture) ends; V8 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0096.jpg`

**t=21.48s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0044.jpg`

**t=22.31s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0046.jpg`

**t=23.57s** — events: V1 cut out; V1 cut in; V8 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0048.jpg`

**t=24.69s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0050.jpg`

**t=26.32s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0054.jpg`

**t=27.36s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0056.jpg`

**t=28.74s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0058.jpg`

**t=30.07s** — events: V1 cut in; Lumetri Color starts; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0061.jpg`

**t=31.53s** — events: V1 cut out; Lumetri Color ends; V2 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0064.jpg`

**t=32.62s** — events: V1 cut in; Lumetri Color starts; V2 cut out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0066.jpg`

**t=33.83s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V8 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0069.jpg`

**t=35.41s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V8 cut out; Text(Kosher salt) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0072.jpg`

**t=37.00s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_2fps/frame_0075.jpg`

**t=38.29s** — events: V1 cut out; Lumetri Color ends; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0108.jpg`

**t=39.66s** — events: V1 cut in; V2 cut out; V7 cut out; V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0125.jpg`

**t=43.71s** — events: V1 cut out; V6 cut (adj) out; Lumetri Color ends; V7 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/crab_ragoon_frames_12fps/frame_0173.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
