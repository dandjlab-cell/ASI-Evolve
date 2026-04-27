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
| 1.38–3.34s | V1 |  | — |  |  |  |
| 3.34–3.55s | V2 |  | — |  |  |  |
| 3.34–46.38s | V6 | ADJ | Lumetri Color |  |  |  |
| 3.34–45.46s | V7 |  | — |  |  |  |
| 3.34–4.55s | V8 |  | Text (Bacon) |  |  |  |
| 3.55–3.63s | V2 |  | — |  |  |  |
| 3.63–3.71s | V2 |  | — |  |  |  |
| 3.71–3.80s | V2 |  | — |  |  |  |
| 3.80–3.88s | V2 |  | — |  |  |  |
| 3.88–3.96s | V2 |  | — |  |  |  |
| 3.96–4.05s | V2 |  | — |  |  |  |
| 4.05–4.13s | V2 |  | — |  |  |  |
| 4.13–4.55s | V2 |  | — |  |  |  |
| 4.55–5.00s | V2 |  | — |  |  |  |
| 5.00–5.55s | V1 |  | — |  |  |  |
| 5.00–5.55s | V2 |  | Mask2 (01) |  | static 4-vertex mask |  |
| 5.42–5.67s | V3 | ADJ | Transform (Zoom In) [animated: Scale Height] |  |  |  |
| 5.55–5.67s | V1 |  | Mirror (Main), Mirror (Main), Mirror (Main), Mirror (Main), Replicate (Main) |  |  |  |
| 5.67–6.67s | V1 |  | — |  |  |  |
| 6.67–8.34s | V1 |  | — |  |  |  |
| 8.34–9.84s | V1 |  | — |  |  |  |
| 8.34–9.84s | V8 |  | Text (Yellow onion) |  |  |  |
| 9.84–11.47s | V1 |  | — |  |  |  |
| 11.47–12.89s | V2 |  | — |  |  | 50% |
| 11.47–12.89s | V8 |  | Text (Low-sodium chicken broth) |  |  |  |
| 12.89–14.35s | V1 |  | — |  |  | 50% |
| 12.89–14.35s | V8 |  | Text (Whole milk) |  |  |  |
| 14.35–15.81s | V2 |  | — |  |  | 50% |
| 15.81–17.23s | V1 |  | — |  |  | 50% |
| 15.81–17.23s | V8 |  | Text (Kosher salt) |  |  |  |
| 17.23–18.89s | V2 |  | — |  |  | 50% |
| 17.23–18.89s | V8 |  | Text (Freshly ground black pepper) |  |  |  |
| 18.89–20.52s | V1 |  | — |  |  | 50% |
| 20.52–21.81s | V1 |  | — |  |  |  |
| 21.81–23.98s | V1 |  | — |  |  | 50% |
| 21.81–23.98s | V8 |  | Text (Russet potatoes) |  |  |  |
| 23.98–26.03s | V2 |  | — |  |  |  |
| 26.03–27.82s | V1 |  | — |  |  |  |
| 27.82–32.20s | V1 |  | — |  |  |  |
| 27.82–32.20s | V9 |  | Graphic Parameters | Mash for a\rchunky texture,\ror blend to make\rit smooth! |  |  |
| 32.20–33.53s | V1 |  | — |  |  |  |
| 33.53–35.45s | V1 |  | — |  |  |  |
| 33.53–35.45s | V8 |  | Text (Cheddar cheese) |  |  |  |
| 35.45–36.95s | V1 |  | — |  |  |  |
| 36.95–39.00s | V1 |  | — |  |  |  |
| 36.95–39.00s | V8 |  | Text (Sour cream) |  |  |  |
| 39.00–40.33s | V1 |  | — |  |  |  |
| 40.33–40.54s | V2 |  | — |  |  |  |
| 40.54–40.62s | V2 |  | — |  |  |  |
| 40.62–40.71s | V2 |  | — |  |  |  |
| 40.71–40.79s | V2 |  | — |  |  |  |
| 40.79–40.87s | V2 |  | — |  |  |  |
| 40.87–40.96s | V2 |  | — |  |  |  |
| 40.96–41.37s | V2 |  | — |  |  |  |
| 41.37–43.04s | V1 |  | — |  |  |  |
| 41.37–43.04s | V8 |  | Text (Cheddar cheese) |  |  |  |
| 43.04–44.71s | V1 |  | — |  |  |  |
| 43.04–44.71s | V8 |  | Text (Crumbled bacon) |  |  |  |
| 44.71–46.38s | V1 |  | — |  |  |  |
| 44.71–46.38s | V8 |  | Text (Fresh chives) |  |  |  |
| 45.46–46.38s | V7 |  | — |  |  |  |
| 46.38–48.13s | V1 |  | — |  |  |  |
| 46.38–55.22s | V6 | ADJ | Lumetri Color |  |  |  |
| 46.38–51.30s | V7 |  | — |  |  |  |
| 46.38–48.13s | V8 |  | Text (Freshly ground black pepper) |  |  |  |
| 48.13–50.05s | V1 |  | — |  |  |  |
| 50.05–51.30s | V1 |  | — |  |  |  |
| 51.30–55.22s | V1 |  | — |  |  | 75% |
| 51.30–55.22s | V7 |  | — |  |  |  |

**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**
- **3.34–46.38s**: V6 (Lumetri Color) stacked over V3 (Transform (Zoom In) [animated: Scale Height])

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=1.38s** — events: V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0004.jpg`

**t=3.34s** — events: V1 cut out; V2 cut in; V6 cut (adj) in; Lumetri Color starts; V7 cut in; V8 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0007.jpg`

**t=4.55s** — events: V2 cut out; V2 cut in; V8 cut out; Text(Bacon) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0022.jpg`

**t=5.00s** — events: V1 cut in; V2 cut out; V2 cut in; Mask2(01) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0027.jpg`

**t=5.42s** — events: V3 cut (adj) in; Transform(Zoom In) starts; V1 cut out; V1 cut in; Mirror(Main) starts; Mirror(Main) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0032.jpg`

**t=6.67s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0047.jpg`

**t=8.34s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Yellow onion) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0018.jpg`

**t=9.84s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Yellow onion) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0021.jpg`

**t=11.47s** — events: V1 cut out; V2 cut in; V8 cut in; Text(Low-sodium chicken broth) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0024.jpg`

**t=12.89s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Low-sodium chicken broth) ends; V8 cut in; Text(Whole milk) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0027.jpg`

**t=14.35s** — events: V1 cut out; V2 cut in; V8 cut out; Text(Whole milk) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0030.jpg`

**t=15.81s** — events: V1 cut in; V2 cut out; V8 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0033.jpg`

**t=17.23s** — events: V1 cut out; V2 cut in; V8 cut out; Text(Kosher salt) ends; V8 cut in; Text(Freshly ground black pepper) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0035.jpg`

**t=18.89s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Freshly ground black pepper) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0039.jpg`

**t=20.52s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0042.jpg`

**t=21.81s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Russet potatoes) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0045.jpg`

**t=23.98s** — events: V1 cut out; V2 cut in; V8 cut out; Text(Russet potatoes) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0049.jpg`

**t=26.03s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0053.jpg`

**t=27.82s** — events: V1 cut out; V1 cut in; V9 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0057.jpg`

**t=32.20s** — events: V1 cut out; V1 cut in; V9 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0065.jpg`

**t=33.53s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Cheddar cheese) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0068.jpg`

**t=35.45s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Cheddar cheese) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0072.jpg`

**t=36.95s** — events: V1 cut out; V1 cut in; V8 cut in; Text(Sour cream) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0075.jpg`

**t=39.00s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Sour cream) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0079.jpg`

**t=40.33s** — events: V1 cut out; V2 cut in; V2 cut out; V2 cut in; V2 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0056.jpg`

**t=41.37s** — events: V1 cut in; V2 cut out; V8 cut in; Text(Cheddar cheese) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0069.jpg`

**t=43.04s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Cheddar cheese) ends; V8 cut in; Text(Crumbled bacon) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0087.jpg`

**t=44.71s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Crumbled bacon) ends; V8 cut in; Text(Fresh chives) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0088.jpg`

**t=45.46s** — events: V7 cut out; V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0097.jpg`

**t=46.38s** — events: V1 cut out; V1 cut in; V6 cut (adj) out; Lumetri Color ends; V6 cut (adj) in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0108.jpg`

**t=48.13s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Freshly ground black pepper) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_12fps/frame_0125.jpg`

**t=50.05s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0101.jpg`

**t=51.30s** — events: V1 cut out; V1 cut in; V7 cut out; V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0104.jpg`

**t=55.22s** — events: V1 cut out; V6 cut (adj) out; Lumetri Color ends; V7 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/loaded_baked_potatoes_frames_2fps/frame_0110.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
