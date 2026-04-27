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
| 0.13–0.21s | V2 |  | Lumetri Color |  |  |
| 0.21–0.29s | V2 |  | Lumetri Color |  |  |
| 0.29–0.38s | V2 |  | Lumetri Color |  |  |
| 0.38–0.46s | V2 |  | Lumetri Color |  |  |
| 0.46–0.54s | V2 |  | Lumetri Color |  |  |
| 0.54–0.63s | V2 |  | Lumetri Color |  |  |
| 0.63–0.67s | V2 |  | Lumetri Color |  |  |
| 0.67–0.75s | V2 |  | Lumetri Color |  |  |
| 0.75–0.83s | V2 |  | Lumetri Color |  |  |
| 0.83–0.92s | V2 |  | Lumetri Color |  |  |
| 0.92–1.00s | V2 |  | Lumetri Color |  |  |
| 1.00–1.08s | V2 |  | Lumetri Color |  |  |
| 1.08–1.17s | V2 |  | Lumetri Color |  |  |
| 1.17–1.71s | V2 |  | Lumetri Color |  |  |
| 1.71–3.34s | V1 |  | — |  |  |
| 3.34–4.55s | V2 |  | — |  |  |
| 3.34–36.45s | V6 | ADJ | Lumetri Color |  |  |
| 3.34–32.78s | V7 |  | — |  |  |
| 3.34–4.55s | V8 |  | Text (English cucumber) |  |  |
| 4.55–5.80s | V1 |  | — |  |  |
| 5.80–6.63s | V2 |  | — |  |  |
| 6.63–6.72s | V2 |  | — |  |  |
| 6.72–6.80s | V2 |  | — |  |  |
| 6.80–6.88s | V2 |  | — |  |  |
| 6.88–6.97s | V2 |  | — |  |  |
| 6.97–7.05s | V2 |  | — |  |  |
| 7.05–7.13s | V2 |  | — |  |  |
| 7.13–7.59s | V2 |  | — |  |  |
| 7.59–8.76s | V1 |  | — |  |  |
| 7.59–8.76s | V8 |  | Text (Kosher salt) |  |  |
| 8.76–10.18s | V1 |  | — |  |  |
| 10.18–12.64s | V1 |  | — |  |  |
| 10.18–12.64s | V8 |  | Graphic Parameters | Let cucumbers drain,\r30 minutes to 1 hour |  |
| 12.64–13.85s | V2 |  | — |  |  |
| 12.64–13.85s | V8 |  | Text (Cream cheese) |  |  |
| 13.85–14.81s | V1 |  | — |  |  |
| 13.85–14.81s | V8 |  | Text (Fresh dill) |  |  |
| 14.81–16.02s | V1 |  | — |  |  |
| 14.81–16.02s | V8 |  | Text (Fresh chives) |  |  |
| 16.02–17.10s | V1 |  | — |  |  |
| 16.02–17.10s | V8 |  | Text (Mayonnaise) |  |  |
| 17.10–18.10s | V1 |  | — |  |  |
| 17.10–18.10s | V8 |  | Text (Kosher salt) |  |  |
| 18.10–19.06s | V1 |  | — |  |  |
| 18.10–19.06s | V8 |  | Text (Freshly ground black pepper) |  |  |
| 19.06–19.94s | V1 |  | — |  |  |
| 19.94–20.60s | V1 |  | — |  |  |
| 20.60–21.77s | V1 |  | — |  |  |
| 21.77–22.94s | V2 |  | Lumetri Color |  |  |
| 21.77–22.94s | V8 |  | Text (White sandwich bread) |  |  |
| 22.94–23.82s | V1 |  | — |  |  |
| 22.94–24.61s | V8 |  | Text (Cream cheese mixture) |  |  |
| 23.82–24.61s | V2 |  | Lumetri Color |  |  |
| 24.61–24.73s | V2 |  | Lumetri Color |  |  |
| 24.73–24.82s | V2 |  | Lumetri Color |  |  |
| 24.82–24.90s | V2 |  | Lumetri Color |  |  |
| 24.90–24.98s | V2 |  | Lumetri Color |  |  |
| 24.98–25.07s | V2 |  | Lumetri Color |  |  |
| 25.07–25.15s | V2 |  | Lumetri Color |  |  |
| 25.15–25.23s | V2 |  | Lumetri Color |  |  |
| 25.23–25.28s | V2 |  | Lumetri Color |  |  |
| 25.28–25.36s | V2 |  | Lumetri Color |  |  |
| 25.36–25.44s | V2 |  | Lumetri Color |  |  |
| 25.44–25.53s | V2 |  | Lumetri Color |  |  |
| 25.53–25.61s | V2 |  | Lumetri Color |  |  |
| 25.61–25.69s | V2 |  | Lumetri Color |  |  |
| 25.69–25.78s | V2 |  | Lumetri Color |  |  |
| 25.78–26.61s | V2 |  | Lumetri Color |  |  |
| 26.61–27.36s | V1 |  | — |  |  |
| 27.36–28.11s | V1 |  | — |  |  |
| 28.11–28.95s | V1 |  | — |  |  |
| 28.95–29.74s | V1 |  | — |  |  |
| 29.74–30.78s | V1 |  | — |  |  |
| 30.78–32.78s | V1 |  | — |  |  |
| 32.78–36.45s | V1 |  | — |  |  |
| 32.78–36.45s | V7 |  | — |  |  |

---

### FRAME_ANALYSIS

# Cucumber Tea — Pass 1 Shot List (Part 1, frames 1-52)

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.00 | OVERHEAD | Title card: "Cucumber Sandwiches / the kitchn" over cream-cheese-spread bread with 3 cucumber slices top row | Title-card hero; baseline frame; compilation state A |
| 2 | 0:00.08 | OVERHEAD | Same sandwich, only 1 cucumber slice visible top-left | Compilation state: slice #1 placed |
| 3 | 0:00.17 | OVERHEAD | Same sandwich, 2 cucumber slices top-left | Compilation state: slice #2 added |
| 4 | 0:00.25 | OVERHEAD | 3 cucumber slices top row (matches frame 1) | Compilation state: slice #3 added |
| 5 | 0:00.33 | OVERHEAD | 4 cucumber slices top row | Compilation state: slice #4 added |
| 6 | 0:00.42 | OVERHEAD | 5 cucumber slices across top of sandwich, fully spanning | Compilation state: slice #5 added |
| 7 | 0:00.50 | OVERHEAD | 5 top slices + 4 slices starting second row (overlapping shingle pattern) | Baseline; compilation state: second row begins |
| 8 | 0:00.58 | OVERHEAD | 5 top slices + 2 slices in second row (left side) | Compilation state: 2 in row 2 |
| 9 | 0:00.67 | OVERHEAD | 5 top slices + 4 slices in second row (closer to full) | Compilation state: 4 in row 2 |
| 10 | 0:00.75 | OVERHEAD | 5 top + 5 second-row slices, bread mostly covered | Compilation state: 5 in row 2 |
| 11 | 0:00.83 | OVERHEAD | 5 top + 6 second-row slices, near-complete coverage | Compilation state: 6 in row 2 |
| 12 | 0:00.92 | OVERHEAD | 5 top + 7 second-row slices, nearly full sandwich coverage | Compilation state: 7 in row 2 |
| 13 | 0:01.00 | OVERHEAD | Title sandwich with hand bringing top bread slice down (motion blur), fully covered cucumber base below | Top-slice placement moment; title still on screen |
| 14 | 0:01.08 | OVERHEAD | Fully covered top row (5) + full second row (6-7 slices), title still on | Intermediate before top bread |
| 15 | 0:01.17 | OVERHEAD | Top bread descending with motion blur, cucumber still visible above | Top-slice drop completing |
| 16 | 0:01.50 | FRONT | Hero beauty: stacked cucumber tea sandwich squares on gold-rim plate, marble surface, hand on plate edge | Title card hero front-angle — finished product beauty |
| 17 | 0:02.00 | FRONT | Same hero stack of tea sandwich squares, title still overlaid | Beauty hold — static |
| 18 | 0:02.50 | FRONT | Same hero tea sandwich stack beauty, slight shift | Beauty hold continues |
| 19 | 0:03.00 | FRONT | Hero tea sandwich stack beauty, title has faded/cleared | Title-card end; clean beauty shot |
| 20 | 0:03.50 | OVERHEAD | Hands steadying whole English cucumber on orange cutting board, chef's knife mid-cut trimming end; "English cucumber" text overlay top-left | Ingredient reveal 1 — cucumber end trim; MOGRT/text appears |
| 21 | 0:04.00 | OVERHEAD | Cucumber on board with end piece separated off to right, hand resting on cucumber; "English cucumber" text still on | End trimmed; establishing ingredient shot |
| 22 | 0:04.50 | FRONT | Benriner mandoline angled across frame, cucumber being pushed through blade from top, sliced rounds piling below on orange cutting board | Mandoline slicing A — action establishing |
| 23 | 0:05.00 | FRONT | Mandoline mid-slice, cucumber shorter (more consumed), larger pile of slices | Mandoline slicing B — progress |
| 24 | 0:05.50 | FRONT | Mandoline with cucumber near top only small stub visible, pile fuller | Mandoline slicing C — near finished |
| 25 | 0:06.00 | OVERHEAD | Fine-mesh strainer set over glass bowl on marble, hand lowering first stack of cucumber slices into strainer | Transfer to strainer — first deposit |
| 26 | 0:06.50 | OVERHEAD | Strainer holding pile of cucumber rounds in centre, hand out of frame | Baseline; strainer filled — dump hold state A |
| 27 | 0:06.63 | OVERHEAD | Strainer pile, subtle shift — slightly fewer/more organized slices | Dense compilation A (same strainer, state change) |
| 28 | 0:06.72 | OVERHEAD | Strainer pile of slices (same composition) | Dense compilation B |
| 29 | 0:06.80 | OVERHEAD | Strainer pile of slices (same composition) | Dense compilation C |
| 30 | 0:06.88 | OVERHEAD | Strainer with more slices added — pile expands to right | Dense compilation D (slices added state) |
| 31 | 0:07.00 | OVERHEAD | Strainer now fuller, cucumber slices covering nearly the whole mesh surface | Baseline; dump nearly complete |
| 32 | 0:07.05 | OVERHEAD | Strainer near-full, last slices being dropped | Dense compilation E |
| 33 | 0:07.13 | OVERHEAD | Strainer full of cucumber slices (final dump state) | Dense compilation F — final |
| 34 | 0:07.50 | FRONT | Closer 3/4 angle of strainer over bowl, "Kosher salt" text overlay top-left, salt streaming down onto cucumbers | Camera change to front; ingredient callout — salting begins |
| 35 | 0:08.00 | FRONT | Same angle, salt continues falling, small white salt pile visible on slices | Salting B — accumulation |
| 36 | 0:08.50 | FRONT | Salt stream visible mid-air, salt pile slightly larger on slices | Salting C — continues |
| 37 | 0:09.00 | FRONT | Two hands tossing salted cucumber slices in strainer, slices lifted and tumbling, small salt residue visible | Tossing to distribute salt A |
| 38 | 0:09.50 | FRONT | Hands gathering and lifting slices from below, continuing toss | Tossing B — different grip |
| 39 | 0:10.00 | OVERHEAD | Extreme close-up of empty glass bowl interior (bottom of bowl, orange cutting board showing through), strainer visible top-right; "Let cucumbers drain, 30 minutes to 1 hour" text callout bottom-left | Time-passes transition / drain hold — shot A |
| 40 | 0:10.50 | OVERHEAD | Same empty bowl bottom, strainer top-right, drain text overlay | Drain hold B (static, time-lapse feel) |
| 41 | 0:11.00 | OVERHEAD | Same empty bowl, slight framing shift | Drain hold C |
| 42 | 0:11.50 | OVERHEAD | Same empty bowl, drain text still on screen | Drain hold D |
| 43 | 0:12.00 | OVERHEAD | Same empty bowl, drain text callout | Drain hold E (end of montage) |
| 44 | 0:12.50 | OVERHEAD | New clean glass bowl on marble, block of cream cheese on spatula being lowered into bowl from bottom-right; "Cream cheese" text overlay top-left | Cream cheese ingredient intro — placement A |
| 45 | 0:13.00 | OVERHEAD | Cream cheese block fully in centre of bowl on spatula, "Cream cheese" text still on | Cream cheese placed B |
| 46 | 0:13.50 | OVERHEAD | Cream cheese block settled in bowl, spatula being withdrawn | Cream cheese settled C |
| 47 | 0:14.00 | OVERHEAD | Cream cheese block in bowl with pile of chopped fresh dill sprinkled on top, small bowl in top-right dumping; "Fresh dill" text overlay top-left | Fresh dill ingredient intro — sprinkle A |
| 48 | 0:14.50 | OVERHEAD | Cream cheese with dill pile, slightly more dill scattered around | Fresh dill B — settled |
| 49 | 0:15.00 | FRONT | Close 3/4 angle of bowl, hand tipping small glass ramekin pouring stream of chopped chives onto cream-cheese-with-dill mound; "Fresh chives" text overlay top-left | Fresh chives ingredient intro — pour A |
| 50 | 0:15.50 | FRONT | Chives fully dumped, ramekin still overhead, large green pile on cream cheese, scattered chive bits | Fresh chives B — dumped |
| 51 | 0:16.00 | FRONT | Same bowl angle, hand squeezing upside-down mayo bottle, dollop of mayo landing on herb pile; "Mayonnaise" text overlay top-left | Mayonnaise ingredient intro — squeeze A |
| 52 | 0:16.50 | FRONT | Mayo continuing to squeeze, larger dollop forming on the mound | Mayonnaise B — dollop growing |
| 53 | 0:17.00 | FRONT | Butter pile with mound of chopped herbs (chives + dill) on top; salt shaker entering top | MOGRT: "Kosher salt"; mid-pour anticipation |
| 54 | 0:17.50 | FRONT | Same butter/herb mound with white flaky kosher salt landed on center of dill | MOGRT: "Kosher salt"; salt deposited |
| 55 | 0:18.00 | FRONT | Cream cheese/herb pile with coarse ground black pepper on top; pepper grinder visible at top of frame | MOGRT: "Freshly ground black pepper"; camera pulled back slightly (wider crop, letterbox) |
| 56 | 0:18.50 | FRONT | Same pile, more pepper settled, grinder lifted away | MOGRT: "Freshly ground black pepper"; static hold |
| 57 | 0:19.00 | FRONT | Yellow silicone spatula plunging into butter/herb mound in glass bowl | No MOGRT; action shot — mixing begins |
| 58 | 0:19.50 | FRONT | Spatula pressing down on butter/herb pile; cream cheese starting to spread | No MOGRT; mixing continues |
| 59 | 0:20.00 | FRONT | Spatula mixing butter/herbs; visible streaks of green folded into pale butter | Mixing progress — herbs dispersing |
| 60 | 0:20.50 | OVERHEAD | Close-up top-down of yellow spatula folding herb-streaked cream cheese mixture in glass bowl | Camera change to OVERHEAD for mixing |
| 61 | 0:21.00 | OVERHEAD | Spatula continuing to fold/mix herbed cream cheese | Overhead mixing continues |
| 62 | 0:21.50 | OVERHEAD | Spatula smoothing mixed herbed cream cheese — uniformly distributed herb flecks | Mixing nearly complete; smooth finish |
| 63 | 0:22.00 | FRONT | Slice of white sandwich bread held by right hand on orange/terracotta surface | MOGRT: "White sandwich bread"; new ingredient intro — assembly begins |
| 64 | 0:22.50 | FRONT | Same white bread slice, hand still holding right edge | MOGRT: "White sandwich bread"; static hold |
| 65 | 0:23.00 | FRONT | Tight shot: small offset spatula knife spreading herbed cream cheese mound on bread | MOGRT: "Cream cheese mixture"; spread just starting |
| 66 | 0:23.50 | FRONT | Spatula continuing to spread mixture across bread — wider, flatter pile | MOGRT: "Cream cheese mixture"; spreading progresses |
| 67 | 0:24.00 | OVERHEAD | Bread slice fully covered with smoothed herbed cream cheese; hand with butter knife at left | MOGRT: "Cream cheese mixture"; camera change to OVERHEAD; spread complete |
| 68 | 0:24.50 | OVERHEAD | Same bread with spread; TWO cucumber slices appear at top-left (stop-motion start) | No MOGRT; cucumber layout compilation begins — state: 2 slices |
| 69 | 0:24.61 | OVERHEAD | Bread with 1 cucumber slice top-left (stop-motion intermediate) | Dense — compilation state: 1 slice visible |
| 70 | 0:24.69 | OVERHEAD | Bread with 1 cucumber slice (same position, slight shift or same pose) | Dense — compilation state: 1 slice |
| 71 | 0:24.78 | OVERHEAD | Bread with 2 cucumber slices laid top-left | Dense — compilation state: 2 slices |
| 72 | 0:24.86 | OVERHEAD | Bread with 3 cucumber slices across top row | Dense — compilation state: 3 slices |
| 73 | 0:24.94 | OVERHEAD | Bread with 4 cucumber slices, top row filling | Dense — compilation state: 4 slices |
| 74 | 0:25.00 | OVERHEAD | Bread with 7 cucumber slices (top row of 5 + 3 on second row) | Compilation state: 7 slices — biggest jump |
| 75 | 0:25.11 | OVERHEAD | Bread with 6 cucumber slices visible (top row 5 + 1 second row) | Dense — appears to be an earlier state re-shown (stop-motion back-and-forth) |
| 76 | 0:25.19 | OVERHEAD | Bread with 7 cucumber slices (top row 5 + 2 second row) | Dense — compilation state: 7 slices |
| 77 | 0:25.28 | OVERHEAD | Bread with 9 cucumber slices (top row 5 + second row 4) | Dense — compilation state: 9 slices |
| 78 | 0:25.36 | OVERHEAD | Bread with 10 cucumber slices (top row 5 + second row 5) | Dense — compilation state: 10 slices |
| 79 | 0:25.44 | OVERHEAD | Bread with 11 cucumber slices (rows 5+5 + 1 started third row bottom-left) | Dense — compilation state: 11 slices |
| 80 | 0:25.50 | OVERHEAD | Bread with ~14 cucumber slices (rows 5+5+4 nearly filling bottom) | Compilation state: ~14 slices — near complete |
| 81 | 0:25.61 | OVERHEAD | Bread with ~13 cucumber slices (rows 5+5+3) | Dense — compilation state: ~13 slices |
| 82 | 0:25.69 | OVERHEAD | Bread with ~14 cucumber slices (rows 5+5+4) | Dense — compilation state: ~14 slices |
| 83 | 0:25.78 | OVERHEAD | Bread fully covered with cucumber slices (rows 5+5+5 = 15 slices) | Dense — compilation state: fully covered — final |
| 84 | 0:26.00 | OVERHEAD | Second plain white bread slice held between two hands on orange surface | Camera holds OVERHEAD; top slice for sandwich intro |
| 85 | 0:26.50 | FRONT | Assembled sandwich on orange cutting board; chef's knife pressing in to start cut; left crust trimmed off at left | Camera change to FRONT (3/4 side); crust-removal begins |
| 86 | 0:27.00 | FRONT | Same sandwich, knife continuing cut through left side | Crust cut in progress |
| 87 | 0:27.50 | FRONT | Sandwich after first crust cut — trimmed strip visible at left (top crust piece); knife repositioning for bottom cut | Crust piece separated at left |
| 88 | 0:28.00 | FRONT | Sandwich rotated; bottom crust being cut off — trimmed left crust piece now at top-left of board with cucumber visible inside | Cutting second crust; sandwich rotated 90° |
| 89 | 0:28.50 | FRONT | Sandwich after second crust cut; one narrow crust strip visible on left side of board | Second crust removed |
| 90 | 0:29.00 | FRONT | Sandwich with 3 trimmed crust strips stacked to the left; hand pressing down, preparing next cut | All 4 crusts trimmed; moving to portioning |
| 91 | 0:29.50 | FRONT | Crustless sandwich on board, knife making vertical cut down center — two halves starting to separate, cucumber filling visible | Portion cut 1: halving the sandwich vertically |
| 92 | 0:30.00 | FRONT | Same mid-cut, two halves more separated, knife deeper | Halving continues |
| 93 | 0:30.50 | FRONT | Sandwich now fully halved, knife at bottom, both halves clearly separated with cucumber/cream cheese filling showing | Halving complete |
| 94 | 0:31.00 | FRONT | Close front-angle of plated tea sandwiches — stacked finger sandwiches on rimmed cream/gold-edged plate; hand at left edge of plate | Camera change to plated beauty; finished product reveal |
| 95 | 0:31.50 | FRONT | Same plated stack, slight shift — multiple finger sandwiches stacked showing cucumber+cream cheese cross-section | Beauty shot hold |
| 96 | 0:32.00 | FRONT | Same plate, slightly different angle/position — hand nudging plate | Beauty shot continues |
| 97 | 0:32.50 | FRONT | Plate of stacked tea sandwiches, even tighter crop, no hand visible | Beauty hold — cleanest plated shot |
| 98 | 0:33.00 | FRONT | Hero beauty: single finger sandwich held up close to camera; end-card "the kitchn" logo burned in bottom-left | End card begins; hero hold begins |
| 99 | 0:33.50 | FRONT | Same single sandwich held, slight rotation showing cucumber/cream cheese layers clearly | End card logo present; hero continues |
| 100 | 0:34.00 | FRONT | Same hero sandwich, slightly tilted down more, filling exposed | End card logo present |
| 101 | 0:34.50 | FRONT | Hero sandwich held, slightly different angle — subtle turn | End card logo present |
| 102 | 0:35.00 | FRONT | Hero sandwich held, position shift again | End card logo present |
| 103 | 0:35.50 | FRONT | Hero sandwich with further angle tilt revealing more cucumber | End card logo present |
| 104 | 0:36.00 | FRONT | Hero sandwich final angle, cucumber filling clearly visible, end frame | End card logo present — final frame |


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
