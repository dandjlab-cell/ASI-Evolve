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
| 1.54–1.96s | V2 | ADJ | Transform (Zoom In) [animated: Scale Height] |  |  |  |
| 1.75–1.96s | V1 |  | Mirror (Main), Mirror (Main), Mirror (Main), Mirror (Main), Replicate (Main) |  |  | 50% |
| 1.96–3.34s | V1 |  | — |  |  | 50% |
| 3.34–7.51s | V2 |  | — |  |  |  |
| 3.34–40.87s | V5 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |  |
| 3.34–46.09s | V6 | ADJ | Lumetri Color |  |  |  |
| 3.34–42.96s | V7 |  | — |  |  |  |
| 3.34–4.71s | V8 |  | Text (All-purpose flour) |  |  |  |
| 4.71–6.17s | V8 |  | Text (Granulated sugar) |  |  |  |
| 6.17–7.51s | V8 |  | Text (Kosher salt) |  |  |  |
| 7.51–9.13s | V1 |  | — |  |  |  |
| 9.13–10.84s | V2 |  | — |  |  |  |
| 9.13–10.84s | V8 |  | Text (Cold unsalted butter) |  |  |  |
| 10.84–11.80s | V1 |  | — |  |  |  |
| 10.84–13.18s | V9 |  | Graphic Parameters | The butter\rshould be\rthe size\rof a pea! |  |  |
| 11.80–13.18s | V1 |  | — |  |  |  |
| 13.18–14.22s | V1 |  | — |  |  |  |
| 14.22–15.47s | V1 |  | — |  |  |  |
| 14.22–15.47s | V8 |  | Text (Ice water) |  |  |  |
| 15.47–16.39s | V1 |  | — |  |  |  |
| 16.39–19.19s | V1 |  | — |  |  |  |
| 19.19–20.27s | V2 |  | — |  |  |  |
| 20.27–21.52s | V1 |  | — |  |  |  |
| 21.52–22.73s | V1 |  | — |  |  |  |
| 22.73–26.86s | V1 |  | — |  |  |  |
| 26.86–27.86s | V1 |  | — |  |  |  |
| 27.86–29.03s | V1 |  | — |  |  |  |
| 29.03–31.32s | V1 |  | — |  |  | 50% |
| 29.61–31.32s | V8 |  | Graphic Parameters | Refrigerate for at least 1 hour |  |  |
| 31.32–32.62s | V1 |  | — |  |  |  |
| 32.62–33.70s | V1 |  | — |  |  | RAMP (5 keyframes) |
| 32.62–35.20s | V8 |  | Graphic Parameters |  A flour-dusted\rrolling pin\rprevents the\rdough from\rsticking |  |  |
| 33.70–35.20s | V1 |  | — |  |  |  |
| 35.20–36.62s | V1 |  | — |  |  | RAMP (6 keyframes) |
| 36.62–37.54s | V1 |  | Lumetri Color |  |  |  |
| 37.54–39.62s | V1 |  | — |  |  |  |
| 39.62–40.87s | V1 |  | — |  |  |  |
| 40.87–43.04s | V1 |  | — |  |  |  |
| 40.87–46.09s | V5 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |  |
| 42.96–46.09s | V7 |  | — |  |  |  |
| 43.04–44.13s | V1 |  | — |  |  | 50% |
| 44.13–46.09s | V1 |  | Lumetri Color |  |  |  |

**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**
- **3.34–46.09s**: V6 (Lumetri Color) stacked over V5 (Lumetri Color (Green), Lumetri Color)
- **3.34–46.09s**: V6 (Lumetri Color) stacked over V5 (Lumetri Color (Green), Lumetri Color)

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=1.54s** — events: V2 cut (adj) in; Transform(Zoom In) starts; V1 cut in; Mirror(Main) starts; Mirror(Main) starts; Mirror(Main) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0007.jpg`

**t=3.34s** — events: V1 cut out; V2 cut in; V5 cut (adj) in; Lumetri Color(Green) starts; Lumetri Color starts; V6 cut (adj) in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0029.jpg`

**t=4.71s** — events: V8 cut out; Text(All-purpose flour) ends; V8 cut in; Text(Granulated sugar) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0045.jpg`

**t=6.17s** — events: V8 cut out; Text(Granulated sugar) ends; V8 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0063.jpg`

**t=7.51s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Kosher salt) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0079.jpg`

**t=9.13s** — events: V1 cut out; V2 cut in; V8 cut in; Text(Cold unsalted butter) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0098.jpg`

**t=10.84s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Cold unsalted butter) ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0119.jpg`

**t=11.80s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0130.jpg`

**t=13.18s** — events: V1 cut out; V1 cut in; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0147.jpg`

**t=14.22s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Ice water) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0159.jpg`

**t=15.47s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Ice water) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0174.jpg`

**t=16.39s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0185.jpg`

**t=19.19s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0219.jpg`

**t=20.27s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0232.jpg`

**t=21.52s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0247.jpg`

**t=22.73s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0261.jpg`

**t=26.86s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0311.jpg`

**t=27.86s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0323.jpg`

**t=29.03s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0337.jpg`

**t=29.61s** — events: V8 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0344.jpg`

**t=31.32s** — events: V1 cut out; V1 cut in; V8 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0364.jpg`

**t=32.62s** — events: V1 cut out; V1 cut in; V8 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0380.jpg`

**t=33.70s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0393.jpg`

**t=35.20s** — events: V1 cut out; V1 cut in; V8 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0411.jpg`

**t=36.62s** — events: V1 cut out; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0428.jpg`

**t=37.54s** — events: V1 cut out; Lumetri Color ends; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0439.jpg`

**t=39.62s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0464.jpg`

**t=40.87s** — events: V1 cut out; V1 cut in; V5 cut (adj) out; Lumetri Color(Green) ends; Lumetri Color ends; V5 cut (adj) in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0479.jpg`

**t=42.96s** — events: V7 cut out; V7 cut in; V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0504.jpg`

**t=44.13s** — events: V1 cut out; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0518.jpg`

**t=46.09s** — events: V1 cut out; Lumetri Color ends; V5 cut (adj) out; Lumetri Color(Green) ends; Lumetri Color ends; V6 cut (adj) out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/flaky_pie_crust_frames_12fps/frame_0540.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
