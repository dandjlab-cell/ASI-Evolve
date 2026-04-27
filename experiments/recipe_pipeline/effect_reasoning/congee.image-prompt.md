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
| 1.54–3.34s | V1 |  | — |  |  |  |
| 3.34–3.96s | V1 |  | — |  |  |  |
| 3.34–39.66s | V6 | ADJ | Lumetri Color |  |  |  |
| 3.34–11.09s | V7 |  | — |  |  |  |
| 3.96–5.30s | V1 |  | — |  |  |  |
| 3.96–5.30s | V8 |  | Text (White rice) |  |  |  |
| 5.30–6.76s | V1 |  | — |  |  |  |
| 5.30–8.38s | V10 |  | Graphic Parameters | Washing\rthe rice leads\rto a creamier\rcongee |  |  |
| 6.76–8.38s | V1 |  | — |  |  |  |
| 8.38–9.68s | V1 |  | — |  |  |  |
| 9.68–11.39s | V1 |  | — |  |  |  |
| 9.68–11.39s | V8 |  | Text (Water) |  |  |  |
| 11.09–12.30s | V7 |  | — |  |  |  |
| 11.39–12.72s | V1 |  | — |  |  |  |
| 12.30–36.41s | V7 |  | — |  |  |  |
| 12.72–13.93s | V1 |  | — |  |  |  |
| 13.93–15.27s | V1 |  | — |  |  |  |
| 13.93–15.27s | V8 |  | Text (Fresh ginger) |  |  |  |
| 15.27–16.56s | V1 |  | — |  |  |  |
| 15.27–16.56s | V8 |  | Text (Garlic) |  |  |  |
| 16.56–18.06s | V1 |  | — |  |  |  |
| 16.56–18.06s | V8 |  | Text (Fresh scallions) |  |  |  |
| 18.06–18.77s | V1 |  | — |  |  |  |
| 18.77–19.77s | V1 |  | — |  |  |  |
| 19.77–21.40s | V1 |  | — |  |  |  |
| 21.40–22.98s | V1 |  | — |  |  |  |
| 21.40–22.98s | V8 |  | Text (Soy sauce) |  |  |  |
| 22.98–24.36s | V1 |  | — |  |  |  |
| 22.98–24.36s | V8 |  | Text (Kosher salt) |  |  |  |
| 24.36–25.73s | V1 |  | — |  |  |  |
| 24.36–25.73s | V8 |  | Text (Toasted sesame oil) |  |  |  |
| 25.73–27.11s | V1 |  | — |  |  |  |
| 25.73–27.11s | V8 |  | Text (Ground white pepper) |  |  |  |
| 27.11–28.53s | V1 |  | — |  |  |  |
| 28.53–30.61s | V1 |  | — |  |  |  |
| 30.61–30.82s | V1 |  | — |  |  |  |
| 30.82–30.91s | V1 |  | — |  |  |  |
| 30.91–30.99s | V1 |  | — |  |  |  |
| 30.99–31.07s | V1 |  | — |  |  |  |
| 31.07–31.16s | V1 |  | — |  |  |  |
| 31.16–31.57s | V1 |  | — |  |  |  |
| 31.57–32.95s | V1 |  | — |  |  |  |
| 31.57–32.95s | V8 |  | Text (Fresh scallions) |  |  |  |
| 32.95–34.58s | V1 |  | — |  |  |  |
| 32.95–34.58s | V8 |  | Text (Toasted sesame oil) |  |  |  |
| 34.58–36.33s | V1 |  | — |  |  |  |
| 36.33–39.66s | V1 |  | — |  |  | 70% |
| 36.91–39.66s | V7 |  | — |  |  |  |

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=1.54s** — events: V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0004.jpg`

**t=3.34s** — events: V1 cut out; V1 cut in; V6 cut (adj) in; Lumetri Color starts; V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0007.jpg`

**t=3.96s** — events: V1 cut out; V1 cut in; V8 cut in; Text(White rice) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0015.jpg`

**t=5.30s** — events: V1 cut out; V1 cut in; V8 cut out; Text(White rice) ends; V10 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0024.jpg`

**t=6.76s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0015.jpg`

**t=8.38s** — events: V1 cut out; V1 cut in; V10 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0018.jpg`

**t=9.68s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Water) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0020.jpg`

**t=11.09s** — events: V7 cut out; V7 cut in; V1 cut out; V1 cut in; V8 cut out; Text(Water) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0023.jpg`

**t=12.30s** — events: V7 cut out; V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0026.jpg`

**t=12.72s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0026.jpg`

**t=13.93s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Fresh ginger) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0029.jpg`

**t=15.27s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Fresh ginger) ends; V8 cut in; Text(Garlic) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0032.jpg`

**t=16.56s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Garlic) ends; V8 cut in; Text(Fresh scallions) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0034.jpg`

**t=18.06s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Fresh scallions) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0037.jpg`

**t=18.77s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0039.jpg`

**t=19.77s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0041.jpg`

**t=21.40s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Soy sauce) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0044.jpg`

**t=22.98s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Soy sauce) ends; V8 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0047.jpg`

**t=24.36s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Kosher salt) ends; V8 cut in; Text(Toasted sesame oil) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0050.jpg`

**t=25.73s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Toasted sesame oil) ends; V8 cut in; Text(Ground white pepper) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0052.jpg`

**t=27.11s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Ground white pepper) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0055.jpg`

**t=28.53s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0058.jpg`

**t=30.61s** — events: V1 cut out; V1 cut in; V1 cut out; V1 cut in; V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0031.jpg`

**t=31.57s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Fresh scallions) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0043.jpg`

**t=32.95s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Fresh scallions) ends; V8 cut in; Text(Toasted sesame oil) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_2fps/frame_0067.jpg`

**t=34.58s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Toasted sesame oil) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0062.jpg`

**t=36.33s** — events: V1 cut out; V1 cut in; V7 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0083.jpg`

**t=36.91s** — events: V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0088.jpg`

**t=39.66s** — events: V1 cut out; V6 cut (adj) out; Lumetri Color ends; V7 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/congee_frames_12fps/frame_0088.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
