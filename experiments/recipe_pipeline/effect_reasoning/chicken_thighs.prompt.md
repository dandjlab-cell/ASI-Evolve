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
| 1.42–2.59s | V1 |  | Lumetri Color, Mask2 (01) [animated: Tracker, Path, Position, Scale Height, Scale Width, Rotation, Anchor Point], Lumetri Color, Mask2 |  | static 9-vertex mask |
| 2.59–3.88s | V1 |  | Lumetri Color |  |  |
| 3.88–5.38s | V1 |  | — |  |  |
| 3.88–45.46s | V7 | ADJ | Lumetri Color |  |  |
| 3.88–42.58s | V8 |  | — |  |  |
| 3.88–5.38s | V9 |  | Graphic Parameters | Garlic |  |
| 5.38–6.55s | V1 |  | — |  |  |
| 5.38–6.55s | V9 |  | Graphic Parameters | Olive oil |  |
| 6.55–7.67s | V1 |  | Lumetri Color |  |  |
| 6.55–7.67s | V9 |  | Graphic Parameters | Soy sauce |  |
| 7.67–9.01s | V1 |  | — |  |  |
| 7.67–9.01s | V9 |  | Graphic Parameters | Light brown sugar |  |
| 9.01–10.14s | V1 |  | Lumetri Color |  |  |
| 10.14–11.39s | V1 |  | Lumetri Color |  |  |
| 10.14–11.39s | V9 |  | Graphic Parameters | Apple cider vinegar |  |
| 11.39–12.43s | V1 |  | — |  |  |
| 11.39–12.43s | V9 |  | Graphic Parameters | Dijon mustard |  |
| 12.43–17.64s | V1 |  | Lumetri Color |  |  |
| 13.14–14.22s | V9 |  | Graphic Parameters | Ground cumin |  |
| 14.22–15.27s | V9 |  | Graphic Parameters | Smoked or regular paprika |  |
| 15.27–16.31s | V9 |  | Graphic Parameters | Kosher salt |  |
| 16.31–17.64s | V9 |  | Graphic Parameters | Freshly ground black pepper |  |
| 17.64–18.56s | V1 |  | Lumetri Color |  |  |
| 18.56–19.85s | V1 |  | Lumetri Color |  |  |
| 19.85–21.52s | V1 |  | — |  |  |
| 21.52–22.65s | V1 |  | — |  |  |
| 21.52–22.65s | V9 |  | Graphic Parameters | Boneless, skinless chicken thighs |  |
| 22.65–23.94s | V1 |  | — |  |  |
| 23.94–24.15s | V1 |  | — |  |  |
| 24.15–24.23s | V1 |  | — |  |  |
| 24.23–24.32s | V1 |  | — |  |  |
| 24.32–24.40s | V1 |  | — |  |  |
| 24.40–24.48s | V1 |  | — |  |  |
| 24.48–24.57s | V1 |  | — |  |  |
| 24.57–24.65s | V1 |  | — |  |  |
| 24.65–24.73s | V1 |  | — |  |  |
| 24.73–25.23s | V1 |  | — |  |  |
| 25.23–26.07s | V1 |  | — |  |  |
| 26.07–27.24s | V1 |  | — |  |  |
| 27.24–28.74s | V1 |  | — |  |  |
| 27.24–28.74s | V9 |  | Graphic Parameters | Refrigerate for at least 2 hours |  |
| 28.74–30.28s | V1 |  | Lumetri Color |  |  |
| 30.28–31.41s | V1 |  | Lumetri Color |  |  |
| 31.41–32.99s | V1 |  | Lumetri Color |  |  |
| 32.99–34.33s | V1 |  | — |  |  |
| 34.33–35.45s | V1 |  | Lumetri Color |  |  |
| 35.45–36.95s | V1 |  | — |  |  |
| 36.95–38.58s | V1 |  | — |  |  |
| 36.95–38.58s | V9 |  | Graphic Parameters | Fresh cilantro |  |
| 38.58–39.75s | V1 |  | Lumetri Color, Mask2 (01) [animated: Tracker, Path, Position, Scale Height, Scale Width, Rotation, Anchor Point], Lumetri Color, Mask2 |  |  |
| 39.75–40.92s | V1 |  | — |  |  |
| 40.92–42.58s | V1 |  | — |  |  |
| 42.58–45.46s | V1 |  | — |  |  |
| 42.58–45.46s | V8 |  | — |  |  |

---

### FRAME_ANALYSIS

# Chicken Thighs FINAL — Pass 1 Shot List

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.0 | FRONT | Tongs flipping chicken on grill pan, grill marks visible | Title card "Grilled Chicken Thighs" + Kitchn logo |
| 2 | 0:00.5 | FRONT | Same grill shot, chicken being turned | Title card still visible |
| 3 | 0:01.0 | FRONT | Chicken thighs on grill, some raw some marked | Beauty open continues |
| 4 | 0:01.5 | OVERHEAD | Knife chopping garlic on white cutting board | Text: "Garlic cloves" |
| 5 | 0:02.0 | OVERHEAD | Chopped garlic scattered on cutting board | Ingredient callout |
| 6 | 0:02.5 | FRONT | Hand scraping chopped garlic into glass bowl | Text: close-up transfer |
| 7 | 0:03.0 | FRONT | Garlic pieces falling into empty glass bowl | Active motion |
| 8 | 0:03.5 | FRONT | Glass bowl with garlic, hand tipping | Garlic settled in bowl |
| 9 | 0:04.0 | FRONT | Olive oil being poured into glass bowl over garlic | Text: "Olive oil" |
| 10 | 0:04.5 | FRONT | Oil stream continuing into bowl | Text: "Olive oil" |
| 11 | 0:05.0 | FRONT | Oil pool forming over garlic in bowl | Pour ending |
| 12 | 0:05.5 | FRONT | Same bowl with oil and garlic, hand withdrawing | Oil settled |
| 13 | 0:06.0 | FRONT | Bowl of oil/garlic, prep area visible | Static hold |
| 14 | 0:06.5 | OVERHEAD | Soy sauce being poured into bowl over oil/garlic | Text: "Soy sauce" |
| 15 | 0:07.0 | OVERHEAD | Soy sauce settling in bowl, dark layer forming | Dark liquid mixing with oil |
| 16 | 0:07.5 | FRONT | Brown sugar being tipped from cup into bowl | Text: "Light brown sugar" |
| 17 | 0:08.0 | FRONT | Brown sugar pile in marinade bowl | TEXT CARD HOLD |
| 18 | 0:08.5 | FRONT | Same brown sugar in bowl, settling | TEXT CARD HOLD |
| 19 | 0:09.0 | FRONT | Brown sugar dissolving slightly in liquids | TEXT CARD HOLD |
| 20 | 0:09.5 | OVERHEAD | Brown sugar mound in marinade, top-down view | TEXT CARD HOLD |
| 21 | 0:10.0 | OVERHEAD | Same view, ingredients settling | TEXT CARD HOLD |
| 22 | 0:10.5 | OVERHEAD | Vinegar being poured into bowl | Text: "Apple cider vinegar" |
| 23 | 0:11.0 | OVERHEAD | Vinegar stream, liquid level rising | TEXT CARD HOLD |
| 24 | 0:11.5 | FRONT | Mustard being spooned into bowl | Text: "Dijon mustard" |
| 25 | 0:12.0 | FRONT | Mustard stream falling into marinade | Close-up pour |
| 26 | 0:12.5 | FRONT | Mustard landing in bowl, thick stream | TEXT CARD HOLD |
| 27 | 0:13.0 | FRONT | Spice being sprinkled into bowl | Text: "Ground cumin" |
| 28 | 0:13.5 | OVERHEAD | Cumin pile in bowl from above | TEXT CARD HOLD |
| 29 | 0:14.0 | OVERHEAD | Paprika being sprinkled over cumin | Text: "Smoked or regular paprika" |
| 30 | 0:14.5 | OVERHEAD | Paprika + cumin mounds visible in marinade | TEXT CARD HOLD |
| 31 | 0:15.0 | OVERHEAD | Salt being pinched over bowl | Text: "Kosher salt" |
| 32 | 0:15.5 | OVERHEAD | Salt crystals landing on spice mounds | TEXT CARD HOLD |
| 33 | 0:16.0 | OVERHEAD | Pepper being ground over bowl | TEXT CARD HOLD |
| 34 | 0:16.5 | OVERHEAD | Ground pepper visible on spice pile | TEXT CARD HOLD |
| 35 | 0:17.0 | OVERHEAD | All spices settled in bowl, pepper/paprika/cumin | Text: "Freshly ground black pepper" |
| 36 | 0:17.5 | FRONT | Whisk entering bowl, beginning to mix | Whisking begins |
| 37 | 0:18.0 | FRONT | Whisk in marinade, blending ingredients | Active whisking |
| 38 | 0:18.5 | FRONT | Marinade partially combined, brown liquid | Whisking continues |
| 39 | 0:19.0 | FRONT | Marinade nearly fully mixed, uniform brown | Almost combined |
| 40 | 0:19.5 | FRONT | Whisking combined marinade, hand stabilizing bowl | Fully whisked |
| 41 | 0:20.0 | FRONT | Brown sugar being poured from bowl — same clip? | Possible ingredient add |
| 42 | 0:20.5 | OVERHEAD | Marinade being poured into zip-top bag on counter | Technique: pour to bag |
| 43 | 0:21.0 | OVERHEAD | Vinegar pour from bottle into marinade in bag | Possible second angle |
| 44 | 0:21.5 | FRONT | Mustard being spooned, close-up with bag | Text: "Dijon mustard" |
| 45 | 0:22.0 | FRONT | Mustard stream into bag/bowl | Close-up technique |
| 46 | 0:22.5 | FRONT | Hand spooning mustard, angled shot | Technique detail |
| 47 | 0:23.0 | FRONT | Spice sprinkle, fast motion | Flash cut, 0.2s beat |
| 48 | 0:23.5 | OVERHEAD | Cumin/spice landing in bowl | Flash cut overhead |
| 49 | 0:24.0 | OVERHEAD | Spice pile in marinade bowl | TEXT CARD HOLD |
| 50 | 0:24.5 | OVERHEAD | Raw chicken thighs in zip-top bag with marinade | Chicken added to bag |
| 51 | 0:25.0 | FRONT | Paprika being sprinkled from hand | Text: "Paprika" |
| 52 | 0:25.5 | FRONT | Paprika landing on surface/marinade | Spice sprinkle |
| 53 | 0:26.0 | FRONT | Prep area, bowl with marinade visible | Static hold or transition |
| 54 | 0:26.5 | FRONT | Salt pinch or seasoning action | Possible salt beat |
| 55 | 0:27.0 | FRONT | Salt/pepper landing in marinade | Seasoning continues |
| 56 | 0:27.5 | FRONT | Pepper grinder over bowl | Pepper grinding |
| 57 | 0:28.0 | FRONT | Pepper being ground over marinade bowl | Close-up technique |
| 58 | 0:28.5 | FRONT | Tongs placing chicken on grill pan | Text: "Kosher salt", placing chicken |
| 59 | 0:29.0 | FRONT | Chicken thighs being arranged on grill with tongs | Placement technique |
| 60 | 0:29.5 | FRONT | Raw marinated chicken on grill pan, tongs arranging | Multiple thighs on grill |
| 61 | 0:30.0 | FRONT | Chicken on grill, tongs pulling away | Placement complete |
| 62 | 0:30.5 | FRONT | Pepper being ground over chicken on grill? | Seasoning on grill |
| 63 | 0:31.0 | FRONT | Same grill view, chicken settling | Static |
| 64 | 0:31.5 | FRONT | Whisking in bowl, close-up | Whisking technique |
| 65 | 0:32.0 | FRONT | Whisk in brown marinade, vigorous motion | Technique beat |
| 66 | 0:32.5 | FRONT | Whisking continuing | Technique |
| 67 | 0:33.0 | FRONT | Whisking slowing, marinade combined | Almost done |
| 68 | 0:33.5 | FRONT | Combined marinade in bowl, whisk visible | Fully combined |
| 69 | 0:34.0 | FRONT | Grilled chicken close-up, grill marks deepening | Grill marks visible |
| 70 | 0:34.5 | FRONT | Chicken with deep caramelized grill marks | Beauty grill shot |
| 71 | 0:35.0 | FRONT | Marinade being poured from bowl | Pour into bag technique |
| 72 | 0:35.5 | FRONT | Marinade pouring into zip-top bag | Technique shot |
| 73 | 0:36.0 | FRONT | Marinade bag being sealed or squeezed | Technique |
| 74 | 0:36.5 | FRONT | Bag with chicken and marinade, massaging | Massage technique |
| 75 | 0:37.0 | FRONT | Chicken patted with paper towel | Pat dry technique |
| 76 | 0:37.5 | FRONT | Paper towel on chicken thigh | Drying technique |
| 77 | 0:38.0 | FRONT | Chicken thigh being dried, close-up | Technique |
| 78 | 0:38.5 | FRONT | Dried chicken thigh, paper towel pulling away | Ready for grill |
| 79 | 0:39.0 | FRONT | Finished chicken on serving plate with herb garnish | Beauty plating |
| 80 | 0:39.5 | FRONT | Same plated chicken, herb garnish visible | Beauty hold |
| 81 | 0:40.0 | FRONT | Plated chicken, slightly wider | Beauty hold |
| 82 | 0:40.5 | FRONT | Plated chicken, beauty shot continues | End sequence |
| 83 | 0:41.0 | FRONT | Chicken on plate, parsley visible | Beauty |
| 84 | 0:41.5 | FRONT | Same beauty, wider angle | End card transition |
| 85 | 0:42.0 | FRONT | Plated chicken, starting to pull wider | End card |
| 86 | 0:42.5 | FRONT | Sliced chicken on cutting board | End card, new shot |
| 87 | 0:43.0 | FRONT | Sliced chicken close-up, juicy interior | End card beauty |
| 88 | 0:43.5 | FRONT | Sliced chicken with herbs on board | End card |
| 89 | 0:44.0 | FRONT | Same sliced chicken, Kitchn logo appearing | End card + logo |
| 90 | 0:44.5 | FRONT | Sliced chicken beauty with Kitchn logo | End card |
| 91 | 0:45.0 | FRONT | Final end card, sliced chicken on cutting board | Kitchn logo prominent |


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
