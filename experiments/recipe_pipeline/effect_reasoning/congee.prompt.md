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
| 1.54–3.34s | V1 |  | — |  |  |
| 3.34–3.96s | V1 |  | — |  |  |
| 3.34–39.66s | V6 | ADJ | Lumetri Color |  |  |
| 3.34–11.09s | V7 |  | — |  |  |
| 3.96–5.30s | V1 |  | — |  |  |
| 3.96–5.30s | V8 |  | Text (White rice) |  |  |
| 5.30–6.76s | V1 |  | — |  |  |
| 5.30–8.38s | V10 |  | Graphic Parameters | Washing\rthe rice leads\rto a creamier\rcongee |  |
| 6.76–8.38s | V1 |  | — |  |  |
| 8.38–9.68s | V1 |  | — |  |  |
| 9.68–11.39s | V1 |  | — |  |  |
| 9.68–11.39s | V8 |  | Text (Water) |  |  |
| 11.09–12.30s | V7 |  | — |  |  |
| 11.39–12.72s | V1 |  | — |  |  |
| 12.30–36.41s | V7 |  | — |  |  |
| 12.72–13.93s | V1 |  | — |  |  |
| 13.93–15.27s | V1 |  | — |  |  |
| 13.93–15.27s | V8 |  | Text (Fresh ginger) |  |  |
| 15.27–16.56s | V1 |  | — |  |  |
| 15.27–16.56s | V8 |  | Text (Garlic) |  |  |
| 16.56–18.06s | V1 |  | — |  |  |
| 16.56–18.06s | V8 |  | Text (Fresh scallions) |  |  |
| 18.06–18.77s | V1 |  | — |  |  |
| 18.77–19.77s | V1 |  | — |  |  |
| 19.77–21.40s | V1 |  | — |  |  |
| 21.40–22.98s | V1 |  | — |  |  |
| 21.40–22.98s | V8 |  | Text (Soy sauce) |  |  |
| 22.98–24.36s | V1 |  | — |  |  |
| 22.98–24.36s | V8 |  | Text (Kosher salt) |  |  |
| 24.36–25.73s | V1 |  | — |  |  |
| 24.36–25.73s | V8 |  | Text (Toasted sesame oil) |  |  |
| 25.73–27.11s | V1 |  | — |  |  |
| 25.73–27.11s | V8 |  | Text (Ground white pepper) |  |  |
| 27.11–28.53s | V1 |  | — |  |  |
| 28.53–30.61s | V1 |  | — |  |  |
| 30.61–30.82s | V1 |  | — |  |  |
| 30.82–30.91s | V1 |  | — |  |  |
| 30.91–30.99s | V1 |  | — |  |  |
| 30.99–31.07s | V1 |  | — |  |  |
| 31.07–31.16s | V1 |  | — |  |  |
| 31.16–31.57s | V1 |  | — |  |  |
| 31.57–32.95s | V1 |  | — |  |  |
| 31.57–32.95s | V8 |  | Text (Fresh scallions) |  |  |
| 32.95–34.58s | V1 |  | — |  |  |
| 32.95–34.58s | V8 |  | Text (Toasted sesame oil) |  |  |
| 34.58–36.33s | V1 |  | — |  |  |
| 36.33–39.66s | V1 |  | — |  |  |
| 36.91–39.66s | V7 |  | — |  |  |

---

### FRAME_ANALYSIS

# Congee V2 — Pass 1 Shot List

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.00 | FRONT | Finished congee in ceramic bowl on marble, green onion garnish, hand on bowl | Title card "Congee / the kitchn" |
| 2 | 0:00.50 | FRONT | Finished congee hero bowl, hand gripping | Title "Congee / the kitchn" overlay |
| 3 | 0:01.00 | FRONT | Finished congee hero bowl, slight motion | Title "Congee / the kitchn" overlay |
| 4 | 0:01.50 | OVERHEAD | White soup spoon dipping into congee bowl | Title "Congee / the kitchn" overlay |
| 5 | 0:02.00 | OVERHEAD | Spoon lifting congee, scallions visible | Title "Congee / the kitchn" overlay |
| 6 | 0:02.50 | OVERHEAD | Spoon lifted higher with heaped congee | Title "Congee / the kitchn" overlay |
| 7 | 0:03.00 | OVERHEAD | Spoon hovering over bowl with full scoop | Title "Congee / the kitchn" overlay |
| 8 | 0:03.50 | FRONT | Empty fine-mesh strainer on marble | Clean product shot, the kitchn logo bottom-right |
| 9 | 0:04.00 | FRONT | Hand pouring white rice from glass measuring cup into strainer | Text overlay "White rice" top-left |
| 10 | 0:04.50 | FRONT | Rice continues pouring, cup tilted | Text overlay "White rice" |
| 11 | 0:05.00 | FRONT | Rice settled in strainer, cup pulling away | Text overlay "White rice" |
| 12 | 0:05.50 | FRONT | Hand rinsing rice under running water in strainer over bowl | Tip callout "Washing the rice leads to a creamier congee" with lightbulb icon |
| 13 | 0:06.00 | FRONT | Hand agitating rice in strainer, water flowing through | Tip callout "Washing the rice leads to a creamier congee" |
| 14 | 0:06.50 | FRONT | Hand continues working rice under water stream | Tip callout "Washing the rice leads to a creamier congee" |
| 15 | 0:07.00 | FRONT | Closer angle — fingers massaging rice in strainer | Tip callout "Washing the rice leads to a creamier congee" |
| 16 | 0:07.50 | FRONT | Hand washing rice, wet skin visible, water droplets | Tip callout "Washing the rice leads to a creamier congee" |
| 17 | 0:08.00 | FRONT | Hand pressing down on rice, water running clearer | Tip callout "Washing the rice leads to a creamier congee" |
| 18 | 0:08.50 | OVERHEAD | Rinsed rice being poured from strainer into cream Dutch oven | No text overlay |
| 19 | 0:09.00 | OVERHEAD | Rice cascading into Dutch oven, pile forming | No text overlay |
| 20 | 0:09.50 | OVERHEAD | Glass measuring cup of water pouring into pot of rice on stove | Text overlay "Water" top-center |
| 21 | 0:10.00 | OVERHEAD | Water continues pouring, rice visible under surface | Text overlay "Water" |
| 22 | 0:10.50 | OVERHEAD | Pouring angle deeper — cup markings (cups) visible | Text overlay "Water" |
| 23 | 0:11.00 | OVERHEAD | Pour finishing, water covering most rice | Text overlay "Water" |
| 24 | 0:11.50 | OVERHEAD | Boiling/simmering rice in Dutch oven, foamy surface | No text overlay |
| 25 | 0:12.00 | OVERHEAD | Continued simmer, foam ring shifting around pot | No text overlay |
| 26 | 0:12.50 | FRONT | Wooden spoon lifting rice out of simmering pot close-up | No text overlay |
| 27 | 0:13.00 | FRONT | Wooden spoon holds softened rice, steam visible | No text overlay |
| 28 | 0:13.50 | FRONT | Wooden spoon tilting, rice spilling gently back in | No text overlay |
| 29 | 0:14.00 | FRONT | Sliced yellow ginger coins dropping into simmering pot | Text overlay "Fresh ginger" top-left |
| 30 | 0:14.50 | FRONT | More ginger slices falling into bubbling rice | Text overlay "Fresh ginger" |
| 31 | 0:15.00 | FRONT | Ginger slices settled in center of pot | Text overlay "Fresh ginger" |
| 32 | 0:15.50 | FRONT | Clear bowl dumping garlic slices into simmering pot | Text overlay "Garlic" top-left |
| 33 | 0:16.00 | FRONT | Garlic slices scattered into the simmer | Text overlay "Garlic" |
| 34 | 0:16.50 | FRONT | Bubbling pot closeup with scallion whites falling in | Text overlay "Fresh scallions" top-left |
| 35 | 0:17.00 | FRONT | Sliced scallions (green + white) landing in pot | Text overlay "Fresh scallions" |
| 36 | 0:17.50 | FRONT | Scallions dispersing across bubbling surface | Text overlay "Fresh scallions" |
| 37 | 0:18.00 | OVERHEAD | Wooden spoon stirring pot of simmering rice with scallion rings visible | No text overlay |
| 38 | 0:18.50 | OVERHEAD | Wider overhead — more broken-down rice, scallions floating, wooden spoon in pot | No text overlay |
| 39 | 0:19.00 | OVERHEAD | Creamy thickened congee in pot, wooden spoon dragging through | No text overlay |
| 40 | 0:19.50 | OVERHEAD | Wooden spoon pulling through thickened congee, texture fully broken down | No text overlay |
| 41 | 0:20.00 | FRONT | Wooden spoon lifting heaping scoop of creamy congee out of pot | No text overlay |
| 42 | 0:20.50 | FRONT | Spoon continues holding scoop, congee dripping | No text overlay |
| 43 | 0:21.00 | FRONT | Closer spoon shot showing broken-grain creamy texture | No text overlay |
| 44 | 0:21.50 | FRONT | Small clear dish pouring soy sauce into congee pot | Text overlay "Soy sauce" top-left |
| 45 | 0:22.00 | FRONT | Soy sauce streaming down into congee forming a dark puddle | Text overlay "Soy sauce" |
| 46 | 0:22.50 | FRONT | Dish tipped further, soy sauce splashing on congee | Text overlay "Soy sauce" |
| 47 | 0:23.00 | FRONT | Soy dish empty, dark swirl on congee surface | Text overlay "Soy sauce" |
| 48 | 0:23.50 | FRONT | Small mound of kosher salt falling onto congee beside soy streaks | Text overlay "Kosher salt" top-left |
| 49 | 0:24.00 | FRONT | Mound of kosher salt settled on congee with soy streak next to it | Text overlay "Kosher salt" |
| 50 | 0:24.50 | FRONT | Amber sesame oil pouring in thin stream onto salt and soy pile | Text overlay "Toasted sesame oil" top-left |
| 51 | 0:25.00 | FRONT | Sesame oil continuing to pour, pooling on top of salt | Text overlay "Toasted sesame oil" |
| 52 | 0:25.50 | FRONT | Sesame oil spreading across top of congee in amber halo | Text overlay "Ground white pepper" top-left |
| 53 | 0:26.00 | FRONT | Small tan mound of white pepper lands on oil-soaked congee | Text overlay "Ground white pepper" |
| 54 | 0:26.50 | FRONT | White pepper mound settled, sesame oil ring around it | Text overlay "Ground white pepper" |
| 55 | 0:27.00 | OVERHEAD | Wooden spoon stirring the seasoning pile (pepper + soy + oil) into congee pot | No text overlay |
| 56 | 0:27.50 | OVERHEAD | Spoon continuing to stir, seasonings blending into congee | No text overlay |
| 57 | 0:28.00 | OVERHEAD | Spoon sweeping through pot, seasonings dispersing | No text overlay |
| 58 | 0:28.50 | FRONT | Wooden spoon lifts big heaped scoop of creamy seasoned congee | No text overlay |
| 59 | 0:29.00 | FRONT | Spoon raised higher, congee clinging | No text overlay |
| 60 | 0:29.50 | FRONT | Spoon full of creamy congee with flecks of scallion visible | No text overlay |
| 61 | 0:30.00 | OVERHEAD | Empty speckled ceramic bowl on marble (plating beat begins) | No text overlay |
| 62 | 0:30.50 | OVERHEAD | Empty bowl, slightly reframed — start of stop-motion dump sequence | No text overlay |
| 63 | 0:30.61 | OVERHEAD | Stop-motion: first dollop of congee appears in bowl | No text overlay — dense frame |
| 64 | 0:30.70 | OVERHEAD | Stop-motion: congee pile grows, filling center of bowl | No text overlay — dense frame |
| 65 | 0:30.78 | OVERHEAD | Stop-motion: congee fills more of the bowl, ginger slice visible | No text overlay — dense frame |
| 66 | 0:30.86 | OVERHEAD | Stop-motion: bowl nearly full, creamy texture obvious | No text overlay — dense frame |
| 67 | 0:30.95 | OVERHEAD | Stop-motion: bowl fully plated with congee | No text overlay — dense frame |
| 68 | 0:31.00 | OVERHEAD | Fully plated congee bowl before garnish | No text overlay |
| 69 | 0:31.11 | OVERHEAD | Same plated bowl, near-identical frame (dense series end) | No text overlay — dense frame |
| 70 | 0:31.50 | FRONT | Close-up of plated bowl, scallions landing on surface | Text overlay "Fresh scallions" top-left |
| 71 | 0:32.00 | FRONT | More scallion slices settled across congee surface | Text overlay "Fresh scallions" |
| 72 | 0:32.50 | FRONT | Scallions fully scattered on finished bowl, fingertip visible top-right | Text overlay "Fresh scallions" |
| 73 | 0:33.00 | FRONT | Thin stream of sesame oil drizzling onto garnished bowl | Text overlay "Toasted sesame oil" top-left |
| 74 | 0:33.50 | FRONT | Sesame oil pooling on surface, amber halo spreading | Text overlay "Toasted sesame oil" |
| 75 | 0:34.00 | FRONT | Finished bowl, oil settled across top with scallions | Text overlay "Toasted sesame oil" |
| 76 | 0:34.50 | OVERHEAD | Slightly wide overhead — garnished bowl drifting into frame on marble | No text overlay |
| 77 | 0:35.00 | OVERHEAD | Overhead close-up of finished bowl, scallions scattered | No text overlay |
| 78 | 0:35.50 | OVERHEAD | Tight overhead of finished bowl with ginger slice visible, fingertip at bottom | No text overlay |
| 79 | 0:36.00 | OVERHEAD | Same close-up overhead, fractionally later | No text overlay |
| 80 | 0:36.50 | FRONT | White soup spoon lifting scoop of finished congee out of bowl | No text overlay |
| 81 | 0:37.00 | FRONT | Spoon raised with heaping scoop, "the kitchn" wordmark appearing | Text overlay "the kitchn" (outro logo building in) |
| 82 | 0:37.50 | FRONT | Outro hero — heaped spoon, "the kitchn" logo + wordmark | Outro logo lockup |
| 83 | 0:38.00 | FRONT | Outro hero frame, identical lockup | Outro logo lockup |
| 84 | 0:38.50 | FRONT | Outro hero frame, spoon drifting slightly | Outro logo lockup |
| 85 | 0:39.00 | FRONT | Final outro frame, "the kitchn" lockup on heaped spoon | Outro logo lockup — end card |

_Total: 85 frames captioned._


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
