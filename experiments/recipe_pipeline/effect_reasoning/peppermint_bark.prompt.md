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
| 1.33–2.17s | V1 |  | — |  |  |
| 2.17–3.00s | V1 |  | — |  |  |
| 3.00–4.71s | V1 |  | — |  |  |
| 4.71–6.30s | V1 |  | — |  |  |
| 4.71–54.18s | V8 |  | — |  |  |
| 4.71–6.30s | V9 |  | Text (Dark chocolate ) |  |  |
| 6.30–7.17s | V1 |  | — |  |  |
| 6.30–9.55s | V9 |  | Graphic Parameters | Microwave until melted, about 2 minutes |  |
| 7.17–8.22s | V1 |  | — |  |  |
| 8.22–9.55s | V1 |  | — |  |  |
| 9.55–11.22s | V1 |  | — |  |  |
| 11.22–12.76s | V1 |  | — |  |  |
| 11.22–12.76s | V9 |  | Text (Peppermint extract) |  |  |
| 12.76–14.72s | V1 |  | — |  |  |
| 14.72–16.14s | V1 |  | — |  |  |
| 16.14–17.64s | V1 |  | — |  |  |
| 17.64–19.56s | V1 |  | — |  |  |
| 17.85–19.56s | V9 |  | Graphic Parameters | Refrigerate for 25 minutes |  |
| 19.56–20.77s | V1 |  | — |  |  |
| 19.56–21.56s | V9 |  | Text (Candy canes) |  |  |
| 20.77–21.56s | V1 |  | — |  |  |
| 21.56–22.40s | V1 |  | — |  |  |
| 22.40–23.44s | V1 |  | — |  |  |
| 23.44–24.65s | V1 |  | — |  |  |
| 24.65–26.03s | V1 |  | — |  |  |
| 26.03–27.53s | V1 |  | — |  |  |
| 26.03–27.53s | V9 |  | Text (White chocolate) |  |  |
| 27.53–28.53s | V1 |  | — |  |  |
| 27.53–29.45s | V9 |  | Graphic Parameters | Microwave until melted, about 1 1/2 minutes |  |
| 28.53–29.45s | V1 |  | — |  |  |
| 29.45–31.45s | V1 |  | — |  |  |
| 31.45–33.12s | V1 |  | — |  |  |
| 31.45–33.12s | V9 |  | Text (Peppermint extract) |  |  |
| 33.12–34.24s | V1 |  | — |  |  |
| 34.24–36.54s | V1 |  | — |  |  |
| 36.54–38.04s | V1 |  | — |  |  |
| 38.04–39.54s | V1 |  | — |  |  |
| 39.54–41.29s | V1 |  | — |  |  |
| 41.29–42.83s | V1 |  | — |  |  |
| 42.83–44.67s | V1 |  | — |  |  |
| 44.67–46.84s | V1 |  | Lumetri Color |  |  |
| 45.13–46.84s | V9 |  | Graphic Parameters | Refrigerate until bark is set,\rabout 35 minutes |  |
| 46.84–47.96s | V1 |  | Lumetri Color |  |  |
| 47.96–48.88s | V1 |  | Lumetri Color |  |  |
| 48.88–50.18s | V1 |  | Lumetri Color |  |  |
| 50.18–51.13s | V1 |  | — |  |  |
| 51.13–52.68s | V1 |  | — |  |  |
| 52.68–54.18s | V1 |  | — |  |  |
| 54.18–56.22s | V1 |  | — |  |  |
| 54.18–58.56s | V8 |  | — |  |  |
| 56.22–58.56s | V1 |  | — |  |  |

---

### FRAME_ANALYSIS

# Peppermint Bark v3 — Pass 1 Shot List (Part 1, frames 1-60)

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.0 | OVERHEAD | Finished peppermint bark pieces on dark blue plate | Title card "Peppermint Bark / the kitchn" overlay |
| 2 | 0:00.5 | OVERHEAD | Finished peppermint bark pieces on blue plate, slight reframe | Title card still up |
| 3 | 0:01.0 | OVERHEAD | Finished peppermint bark pieces on blue plate, slow drift | Title card still up |
| 4 | 0:01.5 | FRONT | Melted dark chocolate poured onto foil-lined pan, pooling | Title card still up |
| 5 | 0:02.0 | FRONT | White chocolate poured on top of set dark chocolate layer | Title card still up |
| 6 | 0:02.5 | FRONT | White chocolate continues pouring, wider pool forming | Title card still up |
| 7 | 0:03.0 | FRONT | Hands snap a finished bark piece in two, close-up | Title card still up |
| 8 | 0:03.5 | FRONT | Hands hold two bark halves apart showing layered cross-section | Title card still up |
| 9 | 0:04.0 | FRONT | Hands hold two bark halves, slightly different angle/reframe | Title card still up (logo drops next frame) |
| 10 | 0:04.5 | OVERHEAD | Empty glass Pyrex mixing bowl | Text overlay "Dark chocolate"; logo lower-right |
| 11 | 0:05.0 | OVERHEAD | Chopped dark chocolate pouring into glass bowl, motion blur | Text overlay "Dark chocolate" |
| 12 | 0:05.5 | OVERHEAD | Dark chocolate mound in bowl, more pieces falling | Text overlay "Dark chocolate" |
| 13 | 0:06.0 | FRONT | Chopped dark chocolate settled in glass bowl, marble counter behind | Text overlay "Dark chocolate"; logo lower-right |
| 14 | 0:06.5 | FRONT | Hand opens mint-green Daewoo microwave door, empty interior | MOGRT card "Microwave until melted, about 2 minutes" enters |
| 15 | 0:07.0 | FRONT | Hand slides glass bowl of chopped chocolate into microwave | MOGRT card "Microwave until melted, about 2 minutes" |
| 16 | 0:07.5 | FRONT | Hand withdraws after placing bowl inside microwave | MOGRT card "Microwave until melted, about 2 minutes" |
| 17 | 0:08.0 | FRONT | Two hands hold bowl of partly-melted chocolate with spatula, on marble counter | MOGRT card "Microwave until melted, about 2 minutes" |
| 18 | 0:08.5 | FRONT | Hands stir melted dark chocolate with grey silicone spatula, close reframe | MOGRT card "Microwave until melted, about 2 minutes" |
| 19 | 0:09.0 | FRONT | Hands continue stirring smooth melted dark chocolate in bowl | MOGRT card "Microwave until melted, about 2 minutes" |
| 20 | 0:09.5 | FRONT | Tight push-in: spatula lifts, thick chocolate ribbons fall back into bowl | MOGRT card drops; possible speed ramp on ribbon drip |
| 21 | 0:10.0 | FRONT | Chocolate dripping off spatula into pool, ribbon thinning | Logo lower-right only |
| 22 | 0:10.5 | FRONT | Chocolate drip continuing, spatula slightly lifted | Logo lower-right only |
| 23 | 0:11.0 | FRONT | Hand tips small glass jar over bowl, first drop of clear extract falling | Text overlay "Peppermint extract" |
| 24 | 0:11.5 | FRONT | Glass jar tipped further, clear peppermint extract drip hangs from rim | Text overlay "Peppermint extract" |
| 25 | 0:12.0 | FRONT | Extract drizzles in a thin stream onto chocolate-smeared bowl rim | Text overlay "Peppermint extract" |
| 26 | 0:12.5 | FRONT | Extract stream continues pouring, finer stream | Text overlay "Peppermint extract" |
| 27 | 0:13.0 | FRONT | Extreme close-up: spatula stirs melted chocolate into thick ribbon swirl | Logo lower-right only; speed-ramp feel on swirl |
| 28 | 0:13.5 | FRONT | Spatula lifts from bowl, chocolate swirl folds and drops | Logo lower-right only; organic flourish |
| 29 | 0:14.0 | FRONT | Glossy chocolate swirl falls back into pool, spatula still lifting | Logo lower-right only |
| 30 | 0:14.5 | OVERHEAD | Melted chocolate pouring from Pyrex measuring cup onto foil-lined pan, pool spreading | Logo lower-right only |
| 31 | 0:15.0 | OVERHEAD | Chocolate pour continues, small pool grown, pitcher still tipped | Logo lower-right only |
| 32 | 0:15.5 | OVERHEAD | Chocolate pour continues with steady stream, pool wider | Logo lower-right only |
| 33 | 0:16.0 | OVERHEAD | Top-down: pastry brush spreads chocolate across foil-lined pan, mostly covered | Logo lower-right only |
| 34 | 0:16.5 | OVERHEAD | Pastry brush continues spreading chocolate layer thinner and wider | Logo lower-right only |
| 35 | 0:17.0 | OVERHEAD | Pastry brush evens out a full, glossy dark chocolate layer | Logo lower-right only |
| 36 | 0:17.5 | FRONT | Very tight profile on the edge of the set dark chocolate layer in foil-lined pan | Logo lower-right only |
| 37 | 0:18.0 | FRONT | Marble countertop texture card | MOGRT card "Refrigerate for 25 minutes" (transition card / elapsed-time beat) |
| 38 | 0:18.5 | FRONT | Marble countertop texture card, same | MOGRT card "Refrigerate for 25 minutes" held |
| 39 | 0:19.0 | FRONT | Marble countertop texture card, same | MOGRT card "Refrigerate for 25 minutes" held |
| 40 | 0:19.5 | FRONT | Hands open a Ziploc freezer bag, empty, on marble | Text overlay "Candy canes" |
| 41 | 0:20.0 | FRONT | First candy cane placed into open Ziploc bag | Text overlay "Candy canes" |
| 42 | 0:20.5 | FRONT | Hand arranges single candy cane at bottom of open bag | Text overlay "Candy canes" |
| 43 | 0:21.0 | FRONT | Several candy canes now in open bag, hand adding more | Text overlay "Candy canes" |
| 44 | 0:21.5 | FRONT | Hand seals the Ziploc bag full of ~5 candy canes | Text overlay "Candy canes" |
| 45 | 0:22.0 | FRONT | Sealed bag of candy canes resting on marble, hands pulling back | Text overlay "Candy canes" (fading) |
| 46 | 0:22.5 | OVERHEAD | Top-down: wooden rolling pin handle pounds candy canes in bag, shards flying | Stop-motion / percussive impact beat |
| 47 | 0:23.0 | OVERHEAD | Rolling pin handle mid-pound, more crushed candy shards visible | Stop-motion / percussive impact beat |
| 48 | 0:23.5 | OVERHEAD | Tight overhead: wooden pin rolls over fully crushed candy cane dust in bag | Possible speed ramp on rolling pass |
| 49 | 0:24.0 | OVERHEAD | Tight overhead: rolling pin continues crushing, shards ground finer | Logo lower-right only |
| 50 | 0:24.5 | FRONT | Hands hold flat bag of crushed candy cane bits, on marble | Logo lower-right only |
| 51 | 0:25.0 | FRONT | Hands display flat sealed bag of finely crushed peppermint dust | Logo lower-right only |
| 52 | 0:25.5 | FRONT | Hands continue holding bag flat; crushed candy fully settled | Logo lower-right only |
| 53 | 0:26.0 | FRONT | White chocolate wafers pouring into empty glass bowl | Text overlay "White chocolate" |
| 54 | 0:26.5 | FRONT | White chocolate wafers filling bowl, more falling | Text overlay "White chocolate" |
| 55 | 0:27.0 | FRONT | Bowl of white chocolate wafers at capacity, pile settled | Text overlay "White chocolate" |
| 56 | 0:27.5 | OVERHEAD | Top-down: full bowl of white chocolate wafers on marble | MOGRT card "Microwave until melted, about 1 1/2 minutes" enters |
| 57 | 0:28.0 | OVERHEAD | Top-down: full bowl of white chocolate wafers, same framing | MOGRT card "Microwave until melted, about 1 1/2 minutes" held |
| 58 | 0:28.5 | OVERHEAD | Top-down: bowl now filled with smooth pale-yellow melted white chocolate | MOGRT card "Microwave until melted, about 1 1/2 minutes" held |
| 59 | 0:29.0 | OVERHEAD | Top-down: grey silicone spatula enters bowl, stirs melted white chocolate | MOGRT card "Microwave until melted, about 1 1/2 minutes" held |
| 60 | 0:29.5 | FRONT | Spatula lifts, thick ribbon of melted white chocolate falls back into bowl | Logo lower-right only; organic flourish / ribbon beat |
| 61 | 0:30.0 | FRONT | Spatula scrapes melted white chocolate back into glass bowl, thick pour | Continuing scrape-pour from part 1 |
| 62 | 0:30.5 | FRONT | Spatula scrape-pour, thick ribbon of white chocolate falls into bowl | Same shot continues |
| 63 | 0:31.0 | FRONT | Spatula scrape-pour continues, ribbon thinning | Same shot |
| 64 | 0:31.5 | OVERHEAD | Hand tips small glass prep bowl over white chocolate, about to pour | Text overlay: "Peppermint extract"; cut to new angle |
| 65 | 0:32.0 | OVERHEAD | Thin stream of peppermint extract pours from prep bowl into white chocolate | Text overlay: "Peppermint extract" |
| 66 | 0:32.5 | OVERHEAD | Stream of peppermint extract continues pouring, swirl forming in chocolate | Text overlay: "Peppermint extract" |
| 67 | 0:33.0 | FRONT | Blue spatula stirs white chocolate in glass bowl, smooth surface | Cut back to front angle |
| 68 | 0:33.5 | FRONT | Spatula stirs white chocolate, folding motion | Same shot |
| 69 | 0:34.0 | FRONT | Extreme close-up of white chocolate being stirred, spatula visible | Push-in or tighter framing |
| 70 | 0:34.5 | FRONT | ECU white chocolate, spatula lifts creating thick ribbon fold | Same tight framing |
| 71 | 0:35.0 | FRONT | ECU white chocolate ribbon falls back into bowl | Same tight framing |
| 72 | 0:35.5 | FRONT | ECU white chocolate ribbon pools, forming folds | Same tight framing |
| 73 | 0:36.0 | FRONT | ECU white chocolate ribbon continues cascading | Likely slow-mo / speed-ramped flourish on ribbon pour |
| 74 | 0:36.5 | OVERHEAD | White chocolate stream pours onto set chocolate layer (dark brown slab in foil-lined pan) | Cut to top-down — transition to new step: layering |
| 75 | 0:37.0 | OVERHEAD | White chocolate stream widens, pool grows on dark chocolate | Same shot; pour flourish |
| 76 | 0:37.5 | OVERHEAD | Pool of white chocolate spreads further across dark chocolate base | Same shot |
| 77 | 0:38.0 | OVERHEAD | White chocolate now covers larger area, hand enters with black-handled offset spatula | Cut — smoothing begins |
| 78 | 0:38.5 | OVERHEAD | Offset spatula spreads white chocolate across dark layer | Same shot |
| 79 | 0:39.0 | OVERHEAD | Offset spatula continues pushing white chocolate to edges, dark crescent still visible | Same shot |
| 80 | 0:39.5 | OVERHEAD | Wide top-down of full foil-lined pan, hand spreads white chocolate with offset spatula | Cut to wider overhead establishing the pan |
| 81 | 0:40.0 | OVERHEAD | Wide overhead, offset spatula smooths white chocolate across pan | Same shot |
| 82 | 0:40.5 | OVERHEAD | Wide overhead, spatula continues smoothing, surface nearly even | Same shot |
| 83 | 0:41.0 | OVERHEAD | Wide overhead, hand pulls spatula out, white chocolate surface smooth | Same shot — spreading nearly complete |
| 84 | 0:41.5 | OVERHEAD | Close-up top-down of smooth white chocolate surface, hand above sprinkling crushed peppermint (pink specks visible) | Cut to tighter overhead — sprinkling flourish |
| 85 | 0:42.0 | OVERHEAD | Close-up overhead, more crushed peppermint pieces landing on white chocolate surface | Same shot — sprinkle continues |
| 86 | 0:42.5 | OVERHEAD | Close-up overhead, denser scatter of peppermint chunks, hand sprinkling from above | Same shot |
| 87 | 0:43.0 | OVERHEAD | Medium overhead (wider), pan half-covered in dense peppermint crumbs, hand sprinkling mid-frame | Cut to wider overhead; speed-ramp likely (sprinkle flourish) |
| 88 | 0:43.5 | OVERHEAD | Medium overhead, peppermint coverage spreading further across white chocolate | Same shot |
| 89 | 0:44.0 | OVERHEAD | Medium overhead, nearly full coverage of peppermint on white chocolate, hand still sprinkling | Same shot |
| 90 | 0:44.5 | OVERHEAD | Wider overhead of full pan with even peppermint coverage, hand exiting frame | Cut to final sprinkle establishing shot |
| 91 | 0:45.0 | OVERHEAD | Blurred marble counter with text card centered | Text overlay: "Refrigerate until bark is set, about 35 minutes" — transition card |
| 92 | 0:45.5 | OVERHEAD | Blurred marble counter, text card still on screen | Text overlay: "Refrigerate until bark is set, about 35 minutes" |
| 93 | 0:46.0 | OVERHEAD | Blurred marble counter, text card still on screen | Text overlay: "Refrigerate until bark is set, about 35 minutes" |
| 94 | 0:46.5 | OVERHEAD | Blurred marble counter, text card still on screen | Text overlay: "Refrigerate until bark is set, about 35 minutes" — extended hold (~2s) |
| 95 | 0:47.0 | FRONT | 3/4 angle of foil-wrapped pan on cutting board, hand lifting foil flap to reveal set peppermint bark | Cut back to bark — post-refrigeration |
| 96 | 0:47.5 | FRONT | 3/4 angle, hand pulls foil edge back further, set bark surface visible | Same shot |
| 97 | 0:48.0 | FRONT | 3/4 angle close-up of set bark on cutting board, chef's knife mid-cut, hand holds bark steady | Cut to cutting — new step |
| 98 | 0:48.5 | FRONT | 3/4 close-up, knife pressing through bark, crack line visible | Same shot, cut progressing |
| 99 | 0:49.0 | FRONT | 3/4 close-up, hand braces bark, knife nearly through, cut line extended | Same shot |
| 100 | 0:49.5 | FRONT | 3/4 close-up, knife tilting for final press-through cut | Same shot |
| 101 | 0:50.0 | OVERHEAD | Top-down of rectangular peppermint bark slab on white cutting board, uncut | Cut to full overhead hero — possibly before-cut establishing |
| 102 | 0:50.5 | OVERHEAD | Top-down of bark now cut into grid of squares (~12 pieces) | Cut to after-cut reveal; fast jump via speed ramp or time-lapse |
| 103 | 0:51.0 | FRONT | Marble counter mostly empty, edge of blue plate with bark pieces visible top-right | Transition shot — hand placing plate |
| 104 | 0:51.5 | FRONT | Blue plate fully in frame, piled high with peppermint bark pieces (white top, pink flakes, dark chocolate bottom) | Beauty hero shot of finished bark |
| 105 | 0:52.0 | FRONT | Blue plate hero, hand entering top-right to lift a piece | Same hero, action begins |
| 106 | 0:52.5 | FRONT | Close-up of hand holding a single bark piece up, rest of plate blurred behind | Cut to ECU hero — showcases layers |
| 107 | 0:53.0 | FRONT | ECU of bark piece held up, detail of pink peppermint, white chocolate, dark chocolate layers | Same shot — beauty hold |
| 108 | 0:53.5 | FRONT | ECU of bark piece held up, slight rotation/tilt | Same shot — beauty hold |
| 109 | 0:54.0 | FRONT | ECU, two hands snap bark piece in half, mid-break, white "the kitchn" logo graphic animates in top-left | End card begins; snap-break action |
| 110 | 0:54.5 | FRONT | ECU, bark piece fully snapped into two halves, clean layered cross-section visible | Logo "the kitchn" overlay centered top |
| 111 | 0:55.0 | FRONT | ECU, two halves held apart, hands pulling slightly | Logo persists |
| 112 | 0:55.5 | FRONT | ECU hero of stacked bark pieces on blue background (tilted plate), peppermint + white + dark layers crisp | Cut to final hero beauty — "the kitchn" logo top-left |
| 113 | 0:56.0 | FRONT | ECU hero of stacked bark, slightly different framing/push | Logo persists |
| 114 | 0:56.5 | FRONT | ECU hero of stacked bark, continuing hold | Logo persists |
| 115 | 0:57.0 | FRONT | ECU hero of stacked bark, continuing hold | Logo persists |
| 116 | 0:57.5 | FRONT | ECU hero of stacked bark, continuing hold | Logo persists — extended final beauty (~3s) |
| 117 | 0:58.0 | FRONT | ECU hero of stacked bark, end of video | Logo persists; final frame |


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
