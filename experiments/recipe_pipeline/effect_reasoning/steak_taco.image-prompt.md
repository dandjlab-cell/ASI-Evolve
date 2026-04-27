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

**Timeline (cuts + effects + masks + MOGRT text, ordered by in-time):**

| Timeline | Track | Adj | Effects | Text overlay | Mask |
|---|---|---|---|---|---|
| 1.25–2.50s | V1 |  | Lumetri Color |  |  |
| 2.50–3.88s | V1 |  | Lumetri Color |  |  |
| 3.88–5.42s | V1 |  | Lumetri Color |  |  |
| 3.88–6.76s | V3 | ADJ | Transform [animated: Position, Scale] |  |  |
| 3.88–63.86s | V7 | ADJ | Lumetri Color |  |  |
| 3.88–61.73s | V8 |  | — |  |  |
| 3.88–5.42s | V9 |  | Graphic Parameters | Orange juice |  |
| 5.42–6.76s | V1 |  | Lumetri Color |  |  |
| 5.42–6.76s | V9 |  | Graphic Parameters | Lime juice |  |
| 6.76–8.01s | V2 |  | — |  |  |
| 6.76–10.30s | V3 | ADJ | Transform [animated: Position, Scale Height] |  |  |
| 6.76–8.01s | V9 |  | Graphic Parameters | Garlic |  |
| 8.01–9.09s | V2 |  | — |  |  |
| 8.01–9.09s | V9 |  | Graphic Parameters | Cilantro |  |
| 9.09–10.30s | V2 |  | — |  |  |
| 9.09–10.30s | V9 |  | Graphic Parameters | Blended chipotle salsa |  |
| 10.30–11.43s | V1 |  | — |  |  |
| 11.43–12.97s | V1 |  | — |  |  |
| 11.43–14.47s | V3 | ADJ | Transform [animated: Position, Scale Height] |  |  |
| 11.43–12.97s | V9 |  | Graphic Parameters | Red onion |  |
| 12.97–14.47s | V1 |  | — |  |  |
| 12.97–14.47s | V9 |  | Graphic Parameters |  Flank steak |  |
| 14.47–15.56s | V1 |  | — |  |  |
| 15.56–17.18s | V1 |  | — |  |  |
| 15.93–17.18s | V9 |  | Graphic Parameters | Refrigerate for 1 to 4 hours |  |
| 17.18–17.98s | V2 |  | — |  |  |
| 17.18–18.85s | V4 |  | Mask2 (02), Mask2 |  |  |
| 17.77–17.98s | V3 |  | — |  |  |
| 17.98–18.06s | V3 |  | — |  |  |
| 18.06–18.10s | V3 |  | — |  |  |
| 18.10–18.18s | V3 |  | — |  |  |
| 18.18–18.27s | V3 |  | — |  |  |
| 18.27–18.35s | V3 |  | — |  |  |
| 18.35–18.85s | V3 |  | — |  |  |
| 18.64–19.06s | V5 | ADJ | Transform (Zoom In) [animated: Scale Height] |  |  |
| 18.85–20.02s | V1 |  | — |  |  |
| 18.85–19.06s | V3 | ADJ | Mirror (Main), Mirror (Main), Mirror (Main), Mirror (Main), Replicate (Main) |  |  |
| 18.85–20.98s | V9 |  | Graphic Parameters | Kosher salt |  |
| 20.02–20.98s | V1 |  | — |  |  |
| 20.98–22.52s | V1 |  | — |  |  |
| 20.98–22.52s | V9 |  | Graphic Parameters | Black pepper |  |
| 22.52–24.11s | V1 |  | — |  |  |
| 22.52–24.11s | V9 |  | Graphic Parameters | Vegetable oil |  |
| 24.11–25.57s | V2 |  | Lumetri Color |  |  |
| 24.11–26.86s | V9 |  | Graphic Parameters | Marinated red onions |  |
| 25.57–26.86s | V1 |  | Lumetri Color |  |  |
| 26.86–27.90s | V2 |  | Lumetri Color |  |  |
| 26.86–29.65s | V3 | ADJ | Transform [animated: Scale Height] |  |  |
| 27.90–29.65s | V2 |  | Lumetri Color |  |  |
| 27.90–29.65s | V9 |  | Graphic Parameters | Marinated flank steak |  |
| 29.65–30.99s | V1 |  | Lumetri Color |  |  |
| 30.99–31.95s | V2 |  | Lumetri Color |  |  |
| 31.95–33.62s | V1 |  | Lumetri Color |  |  |
| 33.62–35.12s | V1 |  | — |  |  |
| 33.62–35.12s | V9 |  | Graphic Parameters |  |  |
| 35.12–37.12s | V1 |  | Lumetri Color |  |  |
| 37.12–38.62s | V1 |  | Lumetri Color |  |  |
| 38.62–39.83s | V1 |  | — |  |  |
| 39.83–41.83s | V1 |  | — |  |  |
| 41.83–43.04s | V2 |  | — |  |  |
| 41.83–44.92s | V9 |  | Graphic Parameters | Corn tortillas |  |
| 43.04–44.92s | V2 |  | — |  |  |
| 44.92–45.42s | V1 |  | — |  |  |
| 45.42–46.09s | V1 |  | — |  |  |
| 46.09–46.96s | V1 |  | — |  |  |
| 46.96–48.17s | V2 |  | — |  |  |
| 46.96–48.17s | V9 |  | Graphic Parameters | Sour cream |  |
| 48.17–49.34s | V1 |  | — |  |  |
| 48.17–49.34s | V9 |  | Graphic Parameters |  |  |
| 49.34–50.13s | V1 |  | — |  |  |
| 50.13–51.01s | V1 |  | — |  |  |
| 51.01–52.22s | V1 |  | — |  |  |
| 52.22–54.14s | V1 |  | — |  |  |
| 52.22–54.14s | V9 |  | Graphic Parameters | Pico de gallo |  |
| 54.14–55.76s | V1 |  | — |  |  |
| 54.14–57.02s | V9 |  | Graphic Parameters | Cotija cheese |  |
| 55.76–57.02s | V1 |  | — |  |  |
| 57.02–58.60s | V1 |  | — |  |  |
| 57.02–58.60s | V9 |  | Graphic Parameters |  |  |
| 58.60–60.19s | V2 |  | — |  |  |
| 58.60–60.19s | V3 | ADJ | Transform [animated: Scale Height] |  |  |
| 60.19–61.73s | V1 |  | — |  |  |
| 61.73–63.86s | V1 |  | — |  |  |
| 61.73–63.86s | V8 |  | — |  |  |

**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**
- **3.88–63.86s**: V7 (Lumetri Color) stacked over V3 (Transform [animated: Position, Scale])
- **3.88–63.86s**: V7 (Lumetri Color) stacked over V3 (Transform [animated: Position, Scale Height])
- **3.88–63.86s**: V7 (Lumetri Color) stacked over V3 (Transform [animated: Position, Scale Height])
- **3.88–63.86s**: V7 (Lumetri Color) stacked over V5 (Transform (Zoom In) [animated: Scale Height])
- **3.88–63.86s**: V7 (Lumetri Color) stacked over V3 (Mirror (Main), Mirror (Main), Mirror (Main), Mirror (Main), Replicate (Main))
- **3.88–63.86s**: V7 (Lumetri Color) stacked over V3 (Transform [animated: Scale Height])
- **3.88–63.86s**: V7 (Lumetri Color) stacked over V3 (Transform [animated: Scale Height])
- **18.64–19.06s**: V5 (Transform (Zoom In) [animated: Scale Height]) stacked over V3 (Mirror (Main), Mirror (Main), Mirror (Main), Mirror (Main), Replicate (Main))

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=1.25s** — events: V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0004.jpg`

**t=2.50s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0006.jpg`

**t=3.88s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V3 cut (adj) in; Transform starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0007.jpg`

**t=5.42s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0026.jpg`

**t=6.76s** — events: V1 cut out; Lumetri Color ends; V2 cut in; V3 cut (adj) out; Transform ends; V3 cut (adj) in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0042.jpg`

**t=8.01s** — events: V2 cut out; V2 cut in; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0057.jpg`

**t=9.09s** — events: V2 cut out; V2 cut in; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0070.jpg`

**t=10.30s** — events: V1 cut in; V2 cut out; V3 cut (adj) out; Transform ends; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0084.jpg`

**t=11.43s** — events: V1 cut out; V1 cut in; V3 cut (adj) in; Transform starts; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0096.jpg`

**t=12.97s** — events: V1 cut out; V1 cut in; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0115.jpg`

**t=14.47s** — events: V1 cut out; V1 cut in; V3 cut (adj) out; Transform ends; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0133.jpg`

**t=15.56s** — events: V1 cut out; V1 cut in; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0032.jpg`

**t=17.18s** — events: V1 cut out; V2 cut in; V4 cut in; Mask2(02) starts; Mask2 starts; V9 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0145.jpg`

**t=17.77s** — events: V3 cut in; V2 cut out; V3 cut out; V3 cut in; V3 cut out; V3 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0152.jpg`

**t=20.98s** — events: V1 cut out; V1 cut in; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0191.jpg`

**t=22.52s** — events: V1 cut out; V1 cut in; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0046.jpg`

**t=24.11s** — events: V1 cut out; V2 cut in; Lumetri Color starts; V9 cut out; Graphic Parameters ends; V9 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0203.jpg`

**t=25.57s** — events: V1 cut in; Lumetri Color starts; V2 cut out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0221.jpg`

**t=26.86s** — events: V1 cut out; Lumetri Color ends; V2 cut in; Lumetri Color starts; V3 cut (adj) in; Transform starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0236.jpg`

**t=27.90s** — events: V2 cut out; Lumetri Color ends; V2 cut in; Lumetri Color starts; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0249.jpg`

**t=29.65s** — events: V1 cut in; Lumetri Color starts; V2 cut out; Lumetri Color ends; V3 cut (adj) out; Transform ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0270.jpg`

**t=30.99s** — events: V1 cut out; Lumetri Color ends; V2 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0286.jpg`

**t=31.95s** — events: V1 cut in; Lumetri Color starts; V2 cut out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0065.jpg`

**t=33.62s** — events: V1 cut out; Lumetri Color ends; V1 cut in; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0298.jpg`

**t=35.12s** — events: V1 cut out; V1 cut in; Lumetri Color starts; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0316.jpg`

**t=37.12s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0075.jpg`

**t=38.62s** — events: V1 cut out; Lumetri Color ends; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0078.jpg`

**t=41.83s** — events: V1 cut out; V2 cut in; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0085.jpg`

**t=44.92s** — events: V1 cut in; V2 cut out; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0091.jpg`

**t=48.17s** — events: V1 cut in; V2 cut out; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0345.jpg`

**t=54.14s** — events: V1 cut out; V1 cut in; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0109.jpg`

**t=57.02s** — events: V1 cut out; V1 cut in; V9 cut out; Graphic Parameters ends; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0115.jpg`

**t=58.60s** — events: V1 cut out; V2 cut in; V3 cut (adj) in; Transform starts; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0352.jpg`

**t=60.19s** — events: V1 cut in; V2 cut out; V3 cut (adj) out; Transform ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_12fps/frame_0371.jpg`

**t=63.86s** — events: V1 cut out; V7 cut (adj) out; Lumetri Color ends; V8 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/steak_taco_frames_2fps/frame_0128.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
