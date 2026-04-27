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
| 1.13–2.42s | V1 |  | — |  |  |
| 2.42–3.88s | V1 |  | Lumetri Color |  |  |
| 3.88–5.17s | V1 |  | — |  |  |
| 3.88–39.50s | V5 | ADJ | Lumetri Color |  |  |
| 3.88–35.37s | V6 |  | — |  |  |
| 3.88–5.17s | V7 |  | Graphic Parameters | Unpeeled garlic cloves |  |
| 5.17–6.55s | V1 |  | Lumetri Color |  |  |
| 6.55–7.72s | V1 |  | — |  |  |
| 7.72–9.51s | V1 |  | Lumetri Color |  |  |
| 7.72–9.51s | V7 |  | Graphic Parameters | Raw pine nuts |  |
| 9.51–10.64s | V1 |  | Lumetri Color |  |  |
| 10.64–11.64s | V1 |  | — |  |  |
| 11.64–12.93s | V1 |  | Lumetri Color |  |  |
| 12.93–13.97s | V1 |  | Lumetri Color |  |  |
| 13.97–15.14s | V1 |  | Lumetri Color |  |  |
| 15.14–16.10s | V1 |  | Lumetri Color |  |  |
| 16.10–16.85s | V1 |  | Lumetri Color |  |  |
| 16.85–17.06s | V1 |  | Lumetri Color |  |  |
| 16.85–18.14s | V7 |  | Graphic Parameters | Fresh basil |  |
| 17.06–17.27s | V1 |  | Lumetri Color |  |  |
| 17.27–18.14s | V1 |  | Lumetri Color |  |  |
| 18.14–19.19s | V1 |  | — |  |  |
| 18.14–19.19s | V7 |  | Graphic Parameters | Lemon zest |  |
| 19.19–20.35s | V1 |  | — |  |  |
| 19.19–20.35s | V7 |  | Graphic Parameters | Parmesan cheese |  |
| 20.35–21.40s | V1 |  | Lumetri Color |  |  |
| 21.40–22.23s | V1 |  | Lumetri Color |  |  |
| 22.23–23.15s | V1 |  | Lumetri Color |  |  |
| 23.15–24.65s | V1 |  | — |  |  |
| 23.15–24.65s | V7 |  | Graphic Parameters | Extra-virgin olive oil |  |
| 24.65–26.03s | V1 |  | — |  |  |
| 24.65–26.03s | V7 |  | Graphic Parameters | Kosher salt |  |
| 26.03–26.99s | V1 |  | — |  |  |
| 26.99–28.11s | V1 |  | Lumetri Color |  |  |
| 28.11–28.82s | V1 |  | Lumetri Color |  |  |
| 28.82–29.61s | V1 |  | — |  |  |
| 29.61–30.95s | V1 |  | — |  |  |
| 30.95–32.41s | V1 |  | — |  |  |
| 32.41–33.78s | V1 |  | — |  |  |
| 33.78–35.37s | V1 |  | — |  |  |
| 33.78–35.37s | V7 |  | Graphic Parameters |  |  |
| 35.37–39.50s | V1 |  | — |  |  |
| 35.37–39.50s | V6 |  | — |  |  |

---

### FRAME_ANALYSIS

# Basil Pesto FINAL — Pass 1 Shot List

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.0 | FRONT | Pesto pouring into glass jar from above | Title card "Basil Pesto" + Kitchn logo |
| 2 | 0:00.5 | FRONT | Pesto stream ending into jar | Title card still visible |
| 3 | 0:01.0 | FRONT | Spaghetti on white plate, pesto dollops at edges | Title card, close-up |
| 4 | 0:01.5 | FRONT | Same pasta plate, slightly tighter | Pesto visible beneath noodles |
| 5 | 0:02.0 | FRONT | Pesto being drizzled onto pasta from top left | Active pour, title card |
| 6 | 0:02.5 | OVERHEAD | Pesto pasta bowl with grated parmesan, hands holding bowl | Finished dish beauty shot, title card |
| 7 | 0:03.0 | OVERHEAD | Same bowl, slight zoom out | Title card fading |
| 8 | 0:03.5 | OVERHEAD | Same bowl, zooming out further | End of title sequence |
| 9 | 0:04.0 | OVERHEAD | Hand placing garlic cloves on white cutting board | Text: "Unpeeled garlic cloves" |
| 10 | 0:04.5 | OVERHEAD | Two unpeeled garlic cloves on cutting board | Ingredient callout, hand withdrawn |
| 11 | 0:05.0 | FRONT | Knife blade approaching garlic clove on board | Close-up, about to crush |
| 12 | 0:05.5 | FRONT | Knife pressing down on garlic clove | Crushing garlic with blade |
| 13 | 0:06.0 | FRONT | Knife flat on garlic, pressing to crush | Continuation of crush |
| 14 | 0:06.5 | OVERHEAD | Hands peeling garlic over stainless steel pan | Breaking skin off clove |
| 15 | 0:07.0 | OVERHEAD | Two crushed garlic cloves in steel pan, hands pulling away | Cloves placed in pan |
| 16 | 0:07.5 | FRONT | Pine nuts in glass bowl above pan with garlic | Text: "Raw pine nuts", about to pour |
| 17 | 0:08.0 | FRONT | Pine nuts cascading into pan over garlic cloves | Mid-pour, active motion |
| 18 | 0:08.5 | FRONT | Pine nuts still pouring, pan nearly full | Text: "Raw pine nuts" |
| 19 | 0:09.0 | FRONT | Pine nuts and garlic settled in pan | Pour complete |
| 20 | 0:09.5 | FRONT | Wooden spoon stirring pine nuts and garlic in pan | Toasting, nuts browning |
| 21 | 0:10.0 | FRONT | Wooden spoon stirring, closer view | Nuts visibly toasted/golden |
| 22 | 0:10.5 | OVERHEAD | Pan tilting, pouring toasted pine nuts onto white plate | Transfer from pan |
| 23 | 0:11.0 | OVERHEAD | Pine nuts and garlic spread on plate, pan pulling away | Cooling on plate |
| 24 | 0:11.5 | FRONT | Hands peeling garlic skin over plate of toasted pine nuts | Close-up, removing skin |
| 25 | 0:12.0 | FRONT | Hands continuing to peel garlic, skin separating | Close-up peeling |
| 26 | 0:12.5 | FRONT | Hand holding peeled garlic clove over pine nuts | Peeled clove visible |
| 27 | 0:13.0 | OVERHEAD | Food processor bowl empty, hand dropping garlic in | Cuisinart, garlic going in |
| 28 | 0:13.5 | OVERHEAD | Food processor with garlic cloves at bottom | Two cloves visible |
| 29 | 0:14.0 | OVERHEAD | Hand pouring toasted pine nuts into food processor | Nuts cascading in from plate |
| 30 | 0:14.5 | OVERHEAD | Pine nuts still pouring into processor from plate | Active pour continues |
| 31 | 0:15.0 | FRONT | Food processor side view, nuts blending, motion blur | First pulse, contents spinning |
| 32 | 0:15.5 | FRONT | Food processor blending, coarser texture visible | Continuing to pulse |
| 33 | 0:16.0 | OVERHEAD | Lid being removed, coarse nut crumble visible inside | Blurry motion, scraping down |
| 34 | 0:16.5 | OVERHEAD | Food processor open, golden crumbly nut/garlic paste | Coarse texture, blade visible |
| 35 | 0:17.0 | OVERHEAD | Fresh basil leaves piled in food processor | Text: "Fresh basil", vibrant green |
| 36 | 0:17.5 | OVERHEAD | Same basil in processor, slightly different angle | Text: "Fresh basil" |
| 37 | 0:18.0 | FRONT | Hand adding lemon zest from small bowl into processor | Text: "Lemon zest", side view |
| 38 | 0:18.5 | FRONT | Lemon zest falling onto basil in processor | Yellow zest on green leaves |
| 39 | 0:19.0 | FRONT | Hand pouring shredded parmesan from metal cup into processor | Text: "Parmesan cheese" |
| 40 | 0:19.5 | FRONT | Parmesan cascading into processor over basil | Text: "Parmesan cheese" |
| 41 | 0:20.0 | FRONT | More parmesan being added, pile growing | Text: "Parmesan cheese" |
| 42 | 0:20.5 | FRONT | Food processor side view, all ingredients layered | Basil, cheese, nut paste visible |
| 43 | 0:21.0 | FRONT | Same layered view, lid going on | About to blend |
| 44 | 0:21.5 | FRONT | Food processor blending, green chunks breaking down | Early blend stage |
| 45 | 0:22.0 | OVERHEAD | Food processor lid, green pesto forming inside | Blending from above, chunky |
| 46 | 0:22.5 | OVERHEAD | Pesto more blended, smoother green texture | Processing continues |
| 47 | 0:23.0 | FRONT | Olive oil pouring from measuring cup into processor feed tube | Text: "Extra-virgin olive oil" |
| 48 | 0:23.5 | FRONT | Oil stream into processor, golden-green | Text: "Extra-virgin olive oil" |
| 49 | 0:24.0 | FRONT | Oil pour continuing into feed tube | Text: "Extra-virgin olive oil" |
| 50 | 0:24.5 | FRONT | Hand pouring kosher salt from small bowl into processor | Text: "Kosher salt" |
| 51 | 0:25.0 | FRONT | Salt streaming into processor feed tube | Text: "Kosher salt" |
| 52 | 0:25.5 | FRONT | Salt pour finishing into processor | Text: "Kosher salt" |
| 53 | 0:26.0 | FRONT | Food processor side view, bright green pesto blending | Smooth, vibrant green |
| 54 | 0:26.5 | FRONT | Food processor, pesto even smoother | Final blend stage |
| 55 | 0:27.0 | OVERHEAD | Lid being removed, smooth pesto in processor bowl | Lid motion blur |
| 56 | 0:27.5 | OVERHEAD | Finished pesto in processor bowl, deep green, blade visible | Smooth and glossy |
| 57 | 0:28.0 | FRONT | Spatula scooping pesto from processor into glass jar | Pesto dripping from spatula |
| 58 | 0:28.5 | FRONT | Spatula with pesto dollop over jar mouth | Active transfer |
| 59 | 0:29.0 | FRONT | Glass jar nearly full of pesto, pesto drip on rim | Hero jar shot |
| 60 | 0:29.5 | FRONT | Hand holding jar of pesto, shot from above-front angle | Texture visible at surface |
| 61 | 0:30.0 | FRONT | Same jar, hand adjusting grip | Slight angle change |
| 62 | 0:30.5 | FRONT | Same jar closeup, pesto surface detail | Continuation |
| 63 | 0:31.0 | FRONT | Spatula scraping pesto from jar onto spaghetti on plate | Pesto dollop landing on pasta |
| 64 | 0:31.5 | FRONT | Spatula dragging pesto across pasta | Pesto spreading |
| 65 | 0:32.0 | FRONT | Spatula pulling pesto across noodles, thick stream | Close-up of pour/spread |
| 66 | 0:32.5 | FRONT | Tongs tossing pesto pasta in green bowl | Fully coated pasta, tong action |
| 67 | 0:33.0 | FRONT | Tongs lifting pesto spaghetti out of bowl | Pasta cascading down |
| 68 | 0:33.5 | FRONT | Pesto spaghetti lifted high, strands falling back | Beauty toss shot |
| 69 | 0:34.0 | FRONT | Pesto pasta in bowl with fresh grated parmesan | Text: "Parmesan cheese" |
| 70 | 0:34.5 | FRONT | Same bowl, parmesan settling | Text: "Parmesan cheese" |
| 71 | 0:35.0 | FRONT | Pesto pasta bowl with parmesan, slightly wider | Text: "Parmesan cheese" |
| 72 | 0:35.5 | FRONT | Bowl being slid toward camera, hand at edge | End card transition, Kitchn logo |
| 73 | 0:36.0 | FRONT | Bowl of pesto pasta with parmesan, Kitchn logo large | End card, closer |
| 74 | 0:36.5 | FRONT | Same bowl, wider view, hand behind | End card, Kitchn logo |
| 75 | 0:37.0 | FRONT | Bowl centered, hand releasing | End card |
| 76 | 0:37.5 | FRONT | Pesto pasta bowl, hand pulling away | End card, Kitchn logo |
| 77 | 0:38.0 | FRONT | Bowl of pesto pasta, wider still | End card, Kitchn logo |
| 78 | 0:38.5 | FRONT | Same bowl, hand barely visible | End card beauty shot |
| 79 | 0:39.0 | FRONT | Final beauty shot of pesto pasta bowl with parmesan | End card, Kitchn logo |


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
