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
| 1.17–2.50s | V1 |  | — |  |  |  |
| 2.50–3.21s | V1 |  | — |  |  |  |
| 3.21–5.21s | V2 |  | — |  |  |  |
| 3.21–62.48s | V8 |  | — |  |  |  |
| 3.21–5.21s | V9 |  | Text (Sweet potatoes) |  |  |  |
| 5.21–7.30s | V1 |  | — |  |  |  |
| 7.30–10.05s | V2 |  | — |  |  |  |
| 8.26–10.05s | V9 |  | Graphic Parameters | Bake at 375°F until tender,\r45 to 60 minutes |  |  |
| 10.05–11.39s | V1 |  | — |  |  | 50% |
| 10.05–11.39s | V9 |  | Text (Flour) |  |  |  |
| 11.39–12.72s | V1 |  | — |  |  |  |
| 11.39–12.72s | V9 |  | Text (Pie dough) |  |  |  |
| 12.72–13.85s | V2 |  | — |  |  | RAMP (6 keyframes) |
| 13.85–15.02s | V2 |  | — |  |  | RAMP (6 keyframes) |
| 15.02–16.31s | V1 |  | — |  |  | RAMP (6 keyframes) |
| 16.31–17.56s | V2 |  | — |  |  |  |
| 17.56–18.73s | V1 |  | — |  |  |  |
| 18.73–20.69s | V1 |  | — |  |  |  |
| 20.69–22.27s | V2 |  | — |  |  | RAMP (6 keyframes) |
| 22.27–24.52s | V2 |  | — |  |  | RAMP (6 keyframes) |
| 23.02–24.52s | V9 |  | Graphic Parameters | Refrigerate for 30 minutes |  |  |
| 24.52–25.73s | V1 |  | — |  |  |  |
| 25.73–27.07s | V1 |  | Lumetri Color |  |  | RAMP (6 keyframes) |
| 27.07–28.24s | V1 |  | Lumetri Color |  |  | RAMP (6 keyframes) |
| 28.24–29.78s | V1 |  | Lumetri Color |  |  | RAMP (6 keyframes) |
| 29.78–30.78s | V2 |  | — |  |  |  |
| 30.78–32.41s | V1 |  | Lumetri Color |  |  |  |
| 32.41–33.78s | V2 |  | — |  |  |  |
| 33.78–35.08s | V2 |  | — |  |  |  |
| 33.78–35.08s | V9 |  | Text (Eggs) |  |  |  |
| 35.08–36.54s | V2 |  | — |  |  |  |
| 35.08–36.54s | V9 |  | Text (Evaporated milk) |  |  |  |
| 36.54–38.58s | V2 |  | — |  |  | RAMP (4 keyframes) |
| 36.54–38.58s | V9 |  | Text (Light brown sugar) |  |  |  |
| 38.58–40.12s | V2 |  | — |  |  |  |
| 38.58–40.12s | V9 |  | Text (Vanilla extract) |  |  |  |
| 40.12–41.37s | V1 |  | Lumetri Color |  |  |  |
| 40.12–41.37s | V9 |  | Text (Ground cinnamon) |  |  |  |
| 41.37–42.58s | V1 |  | Lumetri Color |  |  |  |
| 41.37–42.58s | V9 |  | Text (Ground ginger) |  |  |  |
| 42.58–43.79s | V1 |  | Lumetri Color |  |  |  |
| 42.58–43.79s | V9 |  | Text (Ground nutmeg) |  |  |  |
| 43.79–43.84s | V1 |  | Lumetri Color |  |  |  |
| 43.79–43.84s | V9 |  | Text (Ground nutmeg) |  |  |  |
| 43.84–45.13s | V1 |  | Lumetri Color |  |  |  |
| 43.84–45.13s | V9 |  | Text (Kosher salt) |  |  |  |
| 45.13–47.13s | V2 |  | — |  |  |  |
| 47.13–48.34s | V2 |  | — |  |  |  |
| 48.34–49.80s | V2 |  | — |  |  |  |
| 49.80–50.93s | V1 |  | Lumetri Color |  |  | 50% |
| 50.93–51.76s | V1 |  | Lumetri Color |  |  | 50% |
| 51.76–53.80s | V2 |  | — |  |  |  |
| 52.55–53.80s | V9 |  | Graphic Parameters | Bake until filling is mostly set,\r40 to 60 minutes |  |  |
| 53.80–55.89s | V2 |  | — |  |  |  |
| 55.89–57.27s | V1 |  | — |  |  |  |
| 57.27–58.85s | V2 |  | — |  |  |  |
| 58.85–61.23s | V1 |  | — |  |  |  |
| 61.23–62.48s | V1 |  | — |  |  |  |
| 62.48–66.65s | V1 |  | — |  |  |  |
| 62.48–66.65s | V8 |  | — |  |  |  |

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=2.50s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0007.jpg`

**t=3.21s** — events: V1 cut out; V2 cut in; V8 cut in; V9 cut in; Text(Sweet potatoes) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0016.jpg`

**t=5.21s** — events: V1 cut in; V2 cut out; V9 cut out; Text(Sweet potatoes) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0040.jpg`

**t=7.30s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0052.jpg`

**t=8.26s** — events: V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0064.jpg`

**t=10.05s** — events: V1 cut in; V2 cut out; V9 cut out; Graphic Parameters ends; V9 cut in; Text(Flour) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0085.jpg`

**t=11.39s** — events: V1 cut out; V1 cut in; V9 cut out; Text(Flour) ends; V9 cut in; Text(Pie dough) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0024.jpg`

**t=12.72s** — events: V1 cut out; V2 cut in; V9 cut out; Text(Pie dough) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0026.jpg`

**t=13.85s** — events: V2 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0029.jpg`

**t=15.02s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0031.jpg`

**t=16.31s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0034.jpg`

**t=17.56s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0036.jpg`

**t=18.73s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0038.jpg`

**t=20.69s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0042.jpg`

**t=24.52s** — events: V1 cut in; V2 cut out; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0050.jpg`

**t=25.73s** — events: V1 cut out; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0052.jpg`

**t=27.07s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0055.jpg`

**t=28.24s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0057.jpg`

**t=29.78s** — events: V1 cut out; Lumetri Color ends; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0061.jpg`

**t=30.78s** — events: V1 cut in; Lumetri Color starts; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0063.jpg`

**t=32.41s** — events: V1 cut out; Lumetri Color ends; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0066.jpg`

**t=33.78s** — events: V2 cut out; V2 cut in; V9 cut in; Text(Eggs) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0069.jpg`

**t=35.08s** — events: V2 cut out; V2 cut in; V9 cut out; Text(Eggs) ends; V9 cut in; Text(Evaporated milk) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0071.jpg`

**t=36.54s** — events: V2 cut out; V2 cut in; V9 cut out; Text(Evaporated milk) ends; V9 cut in; Text(Light brown sugar) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0074.jpg`

**t=38.58s** — events: V2 cut out; V2 cut in; V9 cut out; Text(Light brown sugar) ends; V9 cut in; Text(Vanilla extract) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0078.jpg`

**t=40.12s** — events: V1 cut in; Lumetri Color starts; V2 cut out; V9 cut out; Text(Vanilla extract) ends; V9 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0081.jpg`

**t=41.37s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Text(Ground cinnamon) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0084.jpg`

**t=42.58s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Text(Ground ginger) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0086.jpg`

**t=43.79s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Text(Ground nutmeg) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0097.jpg`

**t=45.13s** — events: V1 cut out; Lumetri Color ends; V2 cut in; V9 cut out; Text(Kosher salt) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_12fps/frame_0113.jpg`

**t=49.80s** — events: V1 cut in; Lumetri Color starts; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0101.jpg`

**t=50.93s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0103.jpg`

**t=51.76s** — events: V1 cut out; Lumetri Color ends; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0105.jpg`

**t=53.80s** — events: V2 cut out; V2 cut in; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0109.jpg`

**t=62.48s** — events: V1 cut out; V1 cut in; V8 cut out; V8 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/sweet_potato_pie_frames_2fps/frame_0126.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
