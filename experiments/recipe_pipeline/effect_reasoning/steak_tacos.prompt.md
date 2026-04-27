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

# Steak Tacos — Pass 1 Shot List (2fps, Part 1, frames 1-64)

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.0 | FRONT | Grilled steak on grill pan with charred crust, tongs pressing down, peppers/onions bottom-right | Title card "Grilled Steak Tacos / the kitchn" overlay; steam rising |
| 2 | 0:00.5 | FRONT | Steak continues searing on grill pan, no tongs visible | Title overlay continues; similar composition to frame 1 |
| 3 | 0:01.0 | FRONT | Steak on grill pan, smoke/steam rising heavier, peppers at edge | Title overlay continues; slight camera drift |
| 4 | 0:01.5 | FRONT | Hand reaching in from top-left toward plated steak tacos with pico, cotija, peppers | Title overlay; glamour beauty shot; shallow DOF |
| 5 | 0:02.0 | FRONT | Hand hovering over plated tacos, closer framing on two tacos | Title overlay; slow push-in continuation |
| 6 | 0:02.5 | FRONT | Extreme close-up of single taco held in fingers, pico/cotija/onion visible | Title overlay; beauty hero shot, 16:9 with vertical letterbox bars |
| 7 | 0:03.0 | FRONT | Taco held aloft, same hand, slight rotation/lift | Title overlay; beauty continuation |
| 8 | 0:03.5 | FRONT | Taco held aloft, minor filling shift | Title overlay; final beauty beat before ingredient section |
| 9 | 0:04.0 | FRONT | Hand holding open zip-top bag, measuring cup pouring orange juice in | Text overlay "Orange juice"; kitchn logo bottom-right; marble counter |
| 10 | 0:04.5 | FRONT | Pour continues, juice stream visible, bag held steady | "Orange juice" overlay continues |
| 11 | 0:05.0 | FRONT | Pour finishing, juice pooling at bottom of bag | "Orange juice" overlay continues |
| 12 | 0:05.5 | FRONT | New small cup pouring clearer lime juice into the same bag (now contains OJ pool) | Text overlay changes to "Lime juice"; same setup |
| 13 | 0:06.0 | FRONT | Lime juice pour continuing, thinner stream, bag held open | "Lime juice" overlay continues |
| 14 | 0:06.5 | FRONT | Tail of lime pour, cup nearly empty, yellow pool at bag bottom | "Lime juice" overlay; push-in slight |
| 15 | 0:07.0 | OVERHEAD | Top-down: bag lying on counter, hand holding garlic press squeezing minced garlic into bag | Text overlay "Garlic"; red silicone press tool |
| 16 | 0:07.5 | OVERHEAD | Garlic press squeezing more, mound of minced garlic forming on liquid surface | "Garlic" overlay continues |
| 17 | 0:08.0 | OVERHEAD | Chopped cilantro dumped into bag, forming green pile over garlic/liquid | Text overlay "Cilantro"; same overhead framing |
| 18 | 0:08.5 | OVERHEAD | Cilantro pile settled, slight shift, no hands in frame | "Cilantro" overlay continues; near-static hold |
| 19 | 0:09.0 | OVERHEAD | Dark red-brown chipotle salsa dumped onto cilantro/garlic pile | Text overlay "Blended chipotle salsa" |
| 20 | 0:09.5 | OVERHEAD | Chipotle mound settled, composition similar | "Blended chipotle salsa" overlay continues |
| 21 | 0:10.0 | OVERHEAD | Chipotle/cilantro composition, minor settling | "Blended chipotle salsa" overlay continues |
| 22 | 0:10.5 | FRONT | Camera cuts to side angle on bag standing upright, red spatula stirring marinade inside bag | No overlay; kitchn logo bottom-right; action shot |
| 23 | 0:11.0 | FRONT | Spatula continuing to stir, marinade sloshing, darker mixed color | No overlay; motion continuation |
| 24 | 0:11.5 | FRONT | Hand tilting measuring cup dumping sliced red onion rings into the marinated bag | Text overlay "Red onion"; bag now marbled brown |
| 25 | 0:12.0 | FRONT | Onion rings continuing to drop into bag, cup tilted | "Red onion" overlay continues |
| 26 | 0:12.5 | FRONT | Cup withdrawn, bag standing with onion slices suspended above marinade | "Red onion" overlay; brief hold |
| 27 | 0:13.0 | FRONT | Raw flank steak being lowered into bag with both hands, meat visible red at top | Text overlay "Flank steak"; large cut of meat |
| 28 | 0:13.5 | FRONT | Steak pushed further into bag, more meat visible, hands opening bag wider | "Flank steak" overlay continues |
| 29 | 0:14.0 | FRONT | Steak fully inside bag, hands sealing zipper from top | "Flank steak" overlay continues |
| 30 | 0:14.5 | FRONT | Both hands massaging/squishing sealed bag from above to coat steak in marinade | No overlay; motion shot, marinade visibly mixing |
| 31 | 0:15.0 | FRONT | Continued massaging of bag, color mixing through plastic | No overlay; action continues |
| 32 | 0:15.5 | FRONT | Bag being lifted/shaken, some motion blur on hands | No overlay; slight motion blur suggests real-time speed |
| 33 | 0:16.0 | FRONT | Marble counter clean, out-of-focus blue apron visible upper area | Graphic pill overlay "Refrigerate for 1 to 4 hours"; time-lapse transition |
| 34 | 0:16.5 | FRONT | Same clean counter, nearly identical composition | "Refrigerate for 1 to 4 hours" pill holds |
| 35 | 0:17.0 | OVERHEAD | Top-down: marinated flank steak placed onto sheet pan, hands positioning it, marinade bag in bottom-left corner | No text overlay; kitchn logo bottom-right; scene cut to next step |
| 36 | 0:17.5 | OVERHEAD | Hand continues adjusting steak on sheet pan, slight rotation | No overlay; continuation of placement |
| 37 | 0:18.0 | OVERHEAD | Clean beauty top-down: marinated steak on right, pile of marinated onion rings on left, sheet pan centered | No overlay; glamour/transition shot |
| 38 | 0:18.5 | OVERHEAD | Same top-down but heavy radial motion blur (zoom/spin blur across both halves) | No overlay; speed-ramp/whip transition effect |
| 39 | 0:19.0 | FRONT | Close-up side view of marinated steak on sheet pan, kosher salt sprinkling down from top | Text overlay "Kosher salt"; salt visibly falling |
| 40 | 0:19.5 | FRONT | Salt continuing to fall, grains on meat surface | "Kosher salt" overlay continues |
| 41 | 0:20.0 | FRONT | Salt continuing, subtle increase in salt grains visible on steak | "Kosher salt" overlay continues |
| 42 | 0:20.5 | FRONT | Wider/tighter angle on steak with more visible salt grains sprinkled across top | "Kosher salt" overlay continues |
| 43 | 0:21.0 | FRONT | Similar close-up, finer ground pepper now falling from above onto steak | Text overlay changes to "Black pepper" |
| 44 | 0:21.5 | FRONT | Pepper continuing to fall, subtle darker flecks on meat | "Black pepper" overlay continues |
| 45 | 0:22.0 | FRONT | Pepper fall nearly finishing, steak visibly seasoned | "Black pepper" overlay continues |
| 46 | 0:22.5 | FRONT | Cut to empty cast-iron grill pan on stove, hand holding small glass bowl of oil starting to pour | Text overlay "Vegetable oil" |
| 47 | 0:23.0 | FRONT | Oil stream visibly pouring onto ridges of grill pan | "Vegetable oil" overlay continues |
| 48 | 0:23.5 | FRONT | Oil continuing, pool spreading across grill ridges, drips visible | "Vegetable oil" overlay continues |
| 49 | 0:24.0 | OVERHEAD | Top-down onto empty oiled grill pan, tongs placing loose mound of marinated red onion strands onto grates | Text overlay "Marinated red onions"; blue cast-iron pan handles visible |
| 50 | 0:24.5 | OVERHEAD | Tongs releasing more onion strands, forming small pile center-left of pan | "Marinated red onions" overlay continues |
| 51 | 0:25.0 | OVERHEAD | Tongs withdrawn slightly, onion mound settling | "Marinated red onions" overlay continues |
| 52 | 0:25.5 | FRONT | Tight side view of onions sizzling on grill ridges, light steam rising | "Marinated red onions" overlay; same ingredient, different angle |
| 53 | 0:26.0 | FRONT | Onions continuing to cook, more vibrant color, additional steam | "Marinated red onions" overlay continues |
| 54 | 0:26.5 | FRONT | Onions further wilted, some translucence developing | "Marinated red onions" overlay continues |
| 55 | 0:27.0 | OVERHEAD | Top-down: tongs actively tossing/flipping onion pile, motion blur on onion ribbons | "Marinated red onions" overlay; cooking action shot; steam streaking |
| 56 | 0:27.5 | OVERHEAD | Tongs lifting/turning onion pile, visible charred bits on pan | "Marinated red onions" overlay continues; no label since pile has thinned to show pan |
| 57 | 0:28.0 | OVERHEAD | Raw marinated flank steak lowered onto grill next to cooking onions, tongs holding meat | Text overlay "Marinated flank steak"; steak still raw/red |
| 58 | 0:28.5 | OVERHEAD | Steak settling on grill, both items now cooking together | "Marinated flank steak" overlay continues |
| 59 | 0:29.0 | OVERHEAD | Same composition as 58 but smaller framing (possibly scaled/letterboxed window, zoom-in transition look) | "Marinated flank steak" overlay; letterbox/scale appearance |
| 60 | 0:29.5 | FRONT | Close-up side view of steak sizzling on grill pan, beginning to get char marks, onions visible right | No overlay; beauty searing shot; shallow DOF |
| 61 | 0:30.0 | FRONT | Side close-up continuing, steak developing deeper color, light sizzle | No overlay; hold on sear |
| 62 | 0:30.5 | FRONT | Side close-up, steak slightly shifted, onion ribbons bottom-right in crispy state | No overlay; near-static continuation |
| 63 | 0:31.0 | OVERHEAD | Top-down cut: tongs lifting one side of steak revealing grilled underside, onions pushed to upper-left | No overlay; cooking-action shot showing flip |
| 64 | 0:31.5 | OVERHEAD | Wider top-down: steak being placed back/flipped, wooden board visible top-right, onions piled left, steam rising | No overlay; action/flip completion |
| 65 | 0:32.0 | FRONT | tongs scraping marinade off steak back into cutting board | close angled shot, Staub dutch oven handle visible right |
| 66 | 0:32.5 | FRONT | tongs pressing marinade onto flank steak on cutting board | wider view, hand visible top-left |
| 67 | 0:33.0 | FRONT | marinade bowl lifted away above steak, bits dripping | transition to pan shot; steak fully marinated |
| 68 | 0:33.5 | OVERHEAD | vegetable oil poured onto grill pan with cooked peppers/chiles | "Vegetable oil" text overlay top-left |
| 69 | 0:34.0 | OVERHEAD | oil stream continues into grill pan, peppers at bottom | "Vegetable oil" text overlay persists |
| 70 | 0:34.5 | OVERHEAD | oil pouring into grill pan, pan appears shinier/oilier | "Vegetable oil" text overlay persists |
| 71 | 0:35.0 | FRONT | marinated steak lowered into grill pan by tongs | peppers/onions pushed to bottom-right of pan |
| 72 | 0:35.5 | FRONT | steak placed on grill, sear marks starting to form | tongs repositioning steak |
| 73 | 0:36.0 | FRONT | steak searing on grill pan, grill marks visible | tongs still holding edge of steak |
| 74 | 0:36.5 | FRONT | steak searing, defined grill marks, smoke rising | tongs pulling back from steak |
| 75 | 0:37.0 | FRONT | tight close-up of seared steak with grill marks and peppers beside | very tight macro shot, beauty frame |
| 76 | 0:37.5 | FRONT | tight close-up of seared steak, peppers/onions beside | holds on beauty shot, possible slow push |
| 77 | 0:38.0 | FRONT | very tight close-up of steak on grill with peppers right side | beauty frame, slight shift from previous |
| 78 | 0:38.5 | FRONT | tongs moving sauteed peppers/onions onto cutting board | scene change, peppers being transferred off-heat |
| 79 | 0:39.0 | FRONT | tongs placing peppers/onions pile on wood cutting board | pile forming on board |
| 80 | 0:39.5 | FRONT | tongs lifting away from peppers/onions pile on cutting board | tongs pulling up and away, leaving vegetable mound |
| 81 | 0:40.0 | FRONT | tongs placing cooked steak onto cutting board next to peppers | steak arriving at resting position |
| 82 | 0:40.5 | FRONT | cooked steak resting on cutting board, peppers at bottom-left | beauty hold on grilled flank steak |
| 83 | 0:41.0 | FRONT | cooked flank steak resting on cutting board with peppers front-left | continuation of resting steak beauty shot |
| 84 | 0:41.5 | FRONT | cooked flank steak resting on cutting board, peppers below | holds on rested steak — possible slight zoom or hold |
| 85 | 0:42.0 | OVERHEAD | raw corn tortilla placed on stove grate by hand | "Corn tortillas" text overlay top-left; scene change |
| 86 | 0:42.5 | OVERHEAD | hand retreating from corn tortilla on gas burner grate | "Corn tortillas" text overlay persists |
| 87 | 0:43.0 | FRONT | charred tortilla lifted by fingers over gas flame, another on burner | "Corn tortillas" text overlay persists; flame visible |
| 88 | 0:43.5 | FRONT | tortilla puffed up with char spots cooking over blue flame | "Corn tortillas" text overlay persists, beauty shot of puff |
| 89 | 0:44.0 | FRONT | puffed tortilla toasting over flame, larger char spots forming | "Corn tortillas" text overlay persists |
| 90 | 0:44.5 | FRONT | tortilla continues toasting, char pattern expanding | "Corn tortillas" text overlay persists, hold on beauty shot |
| 91 | 0:45.0 | FRONT | knife slicing into rested flank steak on cutting board | scene change, second steak visible top-left |
| 92 | 0:45.5 | FRONT | knife cutting through end of steak, finishing a slice | same cutting action continues |
| 93 | 0:46.0 | FRONT | knife cutting multiple slices, several strips visible left | slicing through more of the steak — batch of slices visible |
| 94 | 0:46.5 | FRONT | knife continues slicing steak, strips progressively cut | slicing sequence continues |
| 95 | 0:47.0 | OVERHEAD | spoon with sour cream above three charred tortillas on gray plate | "Sour cream" text overlay top-left; scene change |
| 96 | 0:47.5 | OVERHEAD | sour cream dollop dropped onto right tortilla from spoon | "Sour cream" text overlay persists |
| 97 | 0:48.0 | FRONT | sour cream spooned into tortilla shell on plate, tight angle | "Sour cream" text overlay persists, angle change |
| 98 | 0:48.5 | FRONT | spoon spreading sour cream inside tortilla | "Sour cream" text overlay persists |
| 99 | 0:49.0 | FRONT | sour cream spread in two tortilla shells, spoon pulling away | "Sour cream" text overlay persists |
| 100 | 0:49.5 | FRONT | sliced steak placed in sour cream-lined tortilla, tight taco shot | overlay gone; steak showing pink interior, beauty taco frame |
| 101 | 0:50.0 | FRONT | hand placing/arranging steak slices in two sour-cream-lined tacos | fingers arranging toppings, close side view |
| 102 | 0:50.5 | FRONT | assembled tacos with steak resting on sour cream, hand withdrawn | beauty hold on steak tacos before next topping |
| 103 | 0:51.0 | FRONT | sauteed red bell pepper strips added on top of steak in taco | scene: peppers now on steak, close-up beauty |
| 104 | 0:51.5 | FRONT | tight beauty shot of taco with steak and red pepper strips | holds on beauty frame |
| 105 | 0:52.0 | FRONT | spoon dropping pico de gallo onto assembled tacos | "Pico de gallo" text overlay top-left |
| 106 | 0:52.5 | FRONT | spoon continues dropping pico de gallo, salsa forming pile on taco | "Pico de gallo" text overlay persists |
| 107 | 0:53.0 | FRONT | spoon lifting away from taco after adding pico | "Pico de gallo" text overlay persists |
| 108 | 0:53.5 | FRONT | spoon almost out of frame, pico sits on taco with steak/peppers | "Pico de gallo" text overlay persists |
| 109 | 0:54.0 | FRONT | crumbled cotija cheese falling onto pico-topped taco | "Cotija cheese" text overlay top-left |
| 110 | 0:54.5 | FRONT | more cotija sprinkled across taco, cheese coating pico | "Cotija cheese" text overlay persists |
| 111 | 0:55.0 | FRONT | continued cotija sprinkle, cheese pile grows | "Cotija cheese" text overlay persists |
| 112 | 0:55.5 | FRONT | cotija sprinkle continuing on taco | "Cotija cheese" text overlay persists |
| 113 | 0:56.0 | FRONT | beauty hold on cotija-dusted taco with pico, peppers, steak | "Cotija cheese" text overlay persists |
| 114 | 0:56.5 | FRONT | continued beauty hold on finished taco, tight angle | "Cotija cheese" text overlay persists |
| 115 | 0:57.0 | FRONT | single cilantro leaf placed on taco center | "Cilantro" text overlay top-left |
| 116 | 0:57.5 | FRONT | cilantro leaf visible on taco, hand gone | "Cilantro" text overlay persists |
| 117 | 0:58.0 | FRONT | second cilantro leaf added, two leaves on taco | "Cilantro" text overlay persists |
| 118 | 0:58.5 | OVERHEAD | pull-back reveal — three finished tacos on gray plate, hand holds plate edge | scene change, hero reveal shot |
| 119 | 0:59.0 | OVERHEAD | three finished tacos on plate, hand still visible bottom | hero hold, slight subject reposition |
| 120 | 0:59.5 | OVERHEAD | three finished tacos centered on plate, hand mostly out of frame | hero beauty hold |
| 121 | 1:00.0 | FRONT | tight close-up of two finished tacos side-by-side | angle change to side-front hero shot |
| 122 | 1:00.5 | FRONT | tight close-up of two tacos, slightly different framing | continues tight beauty hold |
| 123 | 1:01.0 | FRONT | tight close-up of two tacos with cilantro visible | continuing hold; pink steak edges shown |
| 124 | 1:01.5 | FRONT | hands lifting a taco from the plate, blurred motion | transition to taco-lift beauty shot, shallow focus |
| 125 | 1:02.0 | FRONT | taco held up vertically by hand, showing filling cross-section | "the kitchn" logo overlay with yellow bullseye, end-card style |
| 126 | 1:02.5 | FRONT | taco held up vertically, bigger logo — end card | "the kitchn" logo overlay (larger), end-card |
| 127 | 1:03.0 | FRONT | taco held up, filling visible, logo still present | "the kitchn" logo overlay persists — hold on end-card |
| 128 | 1:03.5 | FRONT | taco held vertically, same end-card composition | "the kitchn" logo overlay persists, final frame |


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
