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
| 1.21–2.54s | V1 |  | — |  |  |
| 2.54–4.21s | V1 |  | — |  |  |
| 4.21–6.01s | V1 |  | — |  |  |
| 4.21–45.55s | V8 |  | — |  |  |
| 4.21–6.01s | V9 |  | Text (Rice Chex cereal) |  |  |
| 6.01–11.01s | V2 |  | — |  |  |
| 6.42–7.55s | V9 |  | Text (Unsalted butter) |  |  |
| 7.55–8.80s | V9 |  | Text (Semisweet chocolate chips) |  |  |
| 8.80–9.97s | V9 |  | Text (Smooth peanut butter) |  |  |
| 9.97–11.01s | V9 |  | Text (Kosher salt) |  |  |
| 11.01–11.97s | V1 |  | — |  |  |
| 11.97–12.76s | V1 |  | — |  |  |
| 11.97–15.43s | V10 |  | Graphic Parameters | Microwave until almost melted,\rabout 2 minutes |  |
| 12.76–13.89s | V1 |  | — |  |  |
| 13.89–15.43s | V2 |  | — |  |  |
| 15.43–16.89s | V1 |  | — |  |  |
| 16.89–17.81s | V1 |  | — |  |  |
| 17.81–19.69s | V1 |  | — |  |  |
| 19.69–21.44s | V2 |  | — |  |  |
| 19.69–21.44s | V9 |  | Text (Vanilla extract) |  |  |
| 21.44–22.81s | V2 |  | — |  |  |
| 22.81–24.02s | V1 |  | — |  |  |
| 24.02–24.98s | V1 |  | — |  |  |
| 24.98–26.23s | V1 |  | — |  |  |
| 26.23–27.11s | V1 |  | — |  |  |
| 27.11–28.36s | V1 |  | — |  |  |
| 28.36–30.16s | V1 |  | — |  |  |
| 28.36–30.16s | V9 |  | Text (Powdered sugar) |  |  |
| 30.16–31.07s | V1 |  | — |  |  |
| 30.16–31.07s | V9 |  | Text (Cereal mixture) |  |  |
| 31.07–32.16s | V1 |  | — |  |  |
| 32.16–33.28s | V1 |  | — |  |  |
| 33.28–34.33s | V1 |  | — |  |  |
| 34.33–35.45s | V1 |  | — |  |  |
| 35.45–36.37s | V1 |  | — |  |  |
| 36.37–37.75s | V1 |  | — |  |  |
| 37.75–39.04s | V2 |  | — |  |  |
| 39.04–40.75s | V2 |  | — |  |  |
| 40.75–42.54s | V1 |  | — |  |  |
| 42.54–44.17s | V1 |  | — |  |  |
| 44.17–48.97s | V2 |  | — |  |  |
| 45.55–48.97s | V8 |  | — |  |  |

---

### FRAME_ANALYSIS

# Puppy Chow v2 — Pass 1 Shot List

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.0 | FRONT | Chocolate peanut butter mixture pouring onto bowl of Chex cereal | Title overlay "Puppy Chow / the kitchn"; glass bowl on marble |
| 2 | 0:00.5 | FRONT | Chocolate drizzle continues landing on plain Chex | Title overlay persists |
| 3 | 0:01.0 | FRONT | Hands with red nails lift yellow bowl of finished powdered puppy chow toward camera | Title overlay; hero beauty shot; wider framing (16:9) |
| 4 | 0:01.5 | FRONT | Hands continue holding yellow bowl of finished puppy chow | Title overlay |
| 5 | 0:02.0 | FRONT | Hands adjust grip, bowl pushed slightly forward | Title overlay |
| 6 | 0:02.5 | FRONT | Extreme close-up of powdered sugar coated puppy chow pieces | Title overlay; shallow DOF |
| 7 | 0:03.0 | FRONT | Extreme close-up of coated pieces, slight push-in | Title overlay; shallow DOF |
| 8 | 0:03.5 | FRONT | Extreme close-up of coated pieces, continued push | Title overlay |
| 9 | 0:04.0 | OVERHEAD | Rice Chex cereal pouring from box into empty Pyrex bowl | Text overlay "Rice Chex cereal"; kitchn logo bottom-right; cereal in motion (blurred) |
| 10 | 0:04.5 | OVERHEAD | Chex continues cascading into bowl, pile building | "Rice Chex cereal" overlay |
| 11 | 0:05.0 | OVERHEAD | More Chex pouring, bowl filling | "Rice Chex cereal" overlay |
| 12 | 0:05.5 | OVERHEAD | Last of Chex pouring from box, nearly empty | "Rice Chex cereal" overlay |
| 13 | 0:06.0 | OVERHEAD | Empty glass bowl on marble countertop | No overlay; reset shot for next ingredient |
| 14 | 0:07.0 | OVERHEAD | Stick of butter appears in empty bowl (stop-motion) | Text overlay "Unsalted butter"; stop-motion insert |
| 15 | 0:07.5 | OVERHEAD | Stick of butter in bowl, static hold | "Unsalted butter" overlay |
| 16 | 0:08.0 | OVERHEAD | Chocolate chips piled in bowl with yellow spatula/butter visible | Text overlay "Semisweet chocolate chips"; stop-motion transition |
| 17 | 0:08.5 | OVERHEAD | Chocolate chips static hold in bowl | "Semisweet chocolate chips" overlay |
| 18 | 0:09.0 | OVERHEAD | Chocolate chips static hold | "Semisweet chocolate chips" overlay |
| 19 | 0:09.5 | OVERHEAD | Scoop of peanut butter added on top of chocolate chips | Text overlay "Smooth peanut butter"; stop-motion |
| 20 | 0:10.0 | OVERHEAD | Peanut butter mound on chocolate chips, tighter crop | "Smooth peanut butter" overlay; slight zoom |
| 21 | 0:10.5 | OVERHEAD | Pinch of salt added on peanut butter mound | Text overlay "Kosher salt"; stop-motion |
| 22 | 0:11.0 | OVERHEAD | Salt on peanut butter, static hold | "Kosher salt" overlay |
| 23 | 0:11.5 | FRONT | Red-nailed hands reach in to pick up bowl of chocolate chips, peanut butter, butter | No overlay; camera switch to side angle |
| 24 | 0:12.0 | FRONT | Hands carry bowl away from counter, motion blur | No overlay; handheld motion |
| 25 | 0:12.5 | FRONT | Hand reaches to open teal/mint Daewoo microwave door | Text overlay "Microwave until almost melted, about 2 minutes" (pill-shape white box) |
| 26 | 0:13.0 | FRONT | Hand pushes on microwave door front (closing it or opening) | "Microwave until almost melted, about 2 minutes" overlay |
| 27 | 0:13.5 | FRONT | Hand places bowl of chocolate chips/peanut butter into microwave | "Microwave until almost melted, about 2 minutes" overlay |
| 28 | 0:14.0 | FRONT | Hand retracts after placing bowl inside microwave | "Microwave until almost melted, about 2 minutes" overlay |
| 29 | 0:14.5 | OVERHEAD | Bowl of melted chocolate/PB enters frame from bottom (camera switch) | "Microwave until almost melted, about 2 minutes" overlay; tilt/pan move |
| 30 | 0:15.0 | OVERHEAD | Hands settle bowl of melted PB + partially-melted chocolate onto counter | Overlay; pieces still visibly unmelted |
| 31 | 0:15.5 | OVERHEAD | Melted mixture, hands retract | "Microwave until almost melted, about 2 minutes" overlay |
| 32 | 0:16.0 | FRONT | Close 3/4 angle: white silicone spatula starts stirring chocolate into melted butter/PB | No overlay; camera switch to low 3/4 angle |
| 33 | 0:16.5 | FRONT | Spatula pushes chocolate through yellow butter/PB mixture, streaks forming | No overlay; stirring action |
| 34 | 0:17.0 | FRONT | Continued stirring, chocolate swirling into mixture | No overlay |
| 35 | 0:17.5 | FRONT | Mixture becoming more uniform brown, spatula sweeping | No overlay |
| 36 | 0:18.0 | FRONT | Nearly blended smooth chocolate-PB sauce, spatula lifting | No overlay |
| 37 | 0:18.5 | FRONT | Spatula lifted out showing silky chocolate-PB coating, bowl below | No overlay; beauty moment |
| 38 | 0:19.0 | FRONT | Spatula with thick chocolate coating, drip forming | No overlay; likely speed-ramp / flourish |
| 39 | 0:19.5 | FRONT | Drip ribbon falls from spatula into bowl of shiny melted mixture | No overlay; organic flourish |
| 40 | 0:20.0 | OVERHEAD | Small glass bowl of dark amber vanilla held above large bowl of melted chocolate | Text overlay "Vanilla extract"; swirls in mixture |
| 41 | 0:20.5 | OVERHEAD | Vanilla starts pouring, dark streak visible entering chocolate | "Vanilla extract" overlay |
| 42 | 0:21.0 | OVERHEAD | Vanilla pour continuing, pool visible | "Vanilla extract" overlay |
| 43 | 0:21.5 | OVERHEAD | Vanilla fully poured, small dish moving away | "Vanilla extract" overlay |
| 44 | 0:22.0 | OVERHEAD | White spatula stirs vanilla into chocolate, hands gripping bowl | No overlay |
| 45 | 0:22.5 | OVERHEAD | Continued stirring, swirl pattern forming | No overlay |
| 46 | 0:23.0 | OVERHEAD | Smooth uniform glossy chocolate-PB sauce in bowl | No overlay |
| 47 | 0:23.5 | FRONT | Chocolate sauce pouring in thick stream onto mound of Chex cereal | No overlay; repeat/callback of opening shot (different framing) |
| 48 | 0:24.0 | FRONT | Chocolate pour lands on Chex, pooling | No overlay |
| 49 | 0:24.5 | FRONT | Chocolate mound grows on cereal, textured ribbon pattern | No overlay |
| 50 | 0:25.0 | FRONT | Chocolate pour continuing, large puddle on cereal | No overlay |
| 51 | 0:25.5 | FRONT | White spatula enters frame and pushes chocolate into cereal | No overlay; camera switch to tighter 3/4 angle for stirring |
| 52 | 0:26.0 | FRONT | Spatula folds chocolate and Chex together, chunks visible | No overlay |
| 53 | 0:26.5 | FRONT | Chex heavily coated, mixing in progress | No overlay |
| 54 | 0:27.0 | FRONT | Spatula lifts mound of coated Chex, heap visible | No overlay |
| 55 | 0:27.5 | FRONT | Wider 3/4 angle: hands grip bowl while spatula folds coated Chex | No overlay; camera pulled back (wider framing) |
| 56 | 0:28.0 | FRONT | Continued folding, coated pieces cascading | No overlay |
| 57 | 0:28.5 | FRONT | Mixture fully coated, uniform brown | No overlay; completed coating |
| 58 | 0:29.0 | FRONT | Large ziploc bag on counter, hand holds open top, bowl of powdered sugar hovering above | Text overlay "Powdered sugar" |
| 59 | 0:29.5 | FRONT | Hands hold bag open, powdered sugar bowl tipping toward opening | "Powdered sugar" overlay |
| 60 | 0:30.0 | FRONT | Powdered sugar dumping from glass bowl into bag | "Powdered sugar" overlay; pour in motion |
| 61 | 0:30.5 | FRONT | Spatula scrapes chocolate-coated Chex into ziploc bag on top of powdered sugar | Text overlay "Cereal mixture" |
| 62 | 0:31.0 | FRONT | Metal scoop/measuring cup dumping more cereal mixture into bag | "Cereal mixture" overlay |
| 63 | 0:31.5 | FRONT | Stainless scoop tipping deeper into bag, cereal cascading | "Cereal mixture" overlay |
| 64 | 0:32.0 | FRONT | Scoop nearly empty, last bits falling into bag | "Cereal mixture" overlay |
| 65 | 0:32.5 | FRONT | Glass bowl of powdered sugar pouring again into bag over cereal | No overlay; second sugar addition |
| 66 | 0:33.0 | FRONT | Heavy pour of powdered sugar cascading into bag | No overlay |
| 67 | 0:33.5 | FRONT | Pour finishing, dust cloud in bag | No overlay |
| 68 | 0:34.0 | FRONT | Both hands gripping top of bag, pressing air out, preparing to seal | No overlay |
| 69 | 0:34.5 | FRONT | Hands sealing zipper of bag | No overlay |
| 70 | 0:35.0 | FRONT | Hands hold sealed bag up and begin tumbling/tossing it | No overlay; wider framing (16:9) |
| 71 | 0:35.5 | FRONT | Bag tilting during toss, powdered sugar visibly coating interior | No overlay; motion |
| 72 | 0:36.0 | FRONT | Bag shaken vigorously, motion blur | No overlay |
| 73 | 0:36.5 | FRONT | Bag resting on marble counter after shake, contents coated in powdered sugar | No overlay |
| 74 | 0:37.0 | FRONT | Bag tipped toward parchment-lined sheet pan, first puppy chow tumbling out | No overlay; camera moved to new angle |
| 75 | 0:37.5 | FRONT | More coated puppy chow pouring onto sheet pan | No overlay |
| 76 | 0:38.0 | OVERHEAD | Sheet pan with mound of powdered puppy chow, spatula reaching in | No overlay; camera switch overhead |
| 77 | 0:38.5 | OVERHEAD | Spatula spreads the pile across the sheet pan | No overlay |
| 78 | 0:39.0 | OVERHEAD | Spatula continues leveling puppy chow across pan | No overlay |
| 79 | 0:39.5 | OVERHEAD | Puppy chow spread wider on pan (zoomed-in crop / push-in) | No overlay; slight reframe |
| 80 | 0:40.0 | OVERHEAD | Pan nearly full, spatula visible at left, hand at right | No overlay |
| 81 | 0:40.5 | OVERHEAD | Continued leveling, pan covered edge-to-edge | No overlay |
| 82 | 0:41.0 | FRONT | Yellow bowl of finished puppy chow entering frame from right, marble bg | No overlay; reveal shot, shallow DOF on counter |
| 83 | 0:41.5 | FRONT | Hand presents yellow bowl of finished puppy chow, push-in | No overlay; hero beauty shot repeat/callback |
| 84 | 0:42.0 | FRONT | Yellow bowl held up, heaped powdered puppy chow | No overlay |
| 85 | 0:42.5 | FRONT | Side 3/4: hand sets yellow bowl down with heaped puppy chow | No overlay; tighter framing |
| 86 | 0:43.0 | FRONT | Extreme close-up inside bowl on powdered puppy chow, shallow DOF | No overlay; beauty macro |
| 87 | 0:43.5 | FRONT | Extreme close-up continues, slight shift in framing | No overlay |
| 88 | 0:44.0 | FRONT | Extreme close-up on cluster of powdered puppy chow | No overlay |
| 89 | 0:44.5 | OVERHEAD | Top-down beauty: bowl of puppy chow centered, marble bg | No overlay; camera switch |
| 90 | 0:45.0 | OVERHEAD | Same top-down bowl, subtle shift (stop-motion/static hold) | No overlay |
| 91 | 0:45.5 | OVERHEAD | Hand enters from top of frame, reaching into bowl | No overlay; end-tag setup |
| 92 | 0:46.0 | OVERHEAD | Two hands enter bowl grabbing puppy chow; "the kitchn" end-tag animating in (partial text) | Animated end-tag overlay appearing |
| 93 | 0:46.5 | OVERHEAD | "the kitchn" logo fully formed, hands rummaging in puppy chow | Full "the kitchn" end-tag with logo |
| 94 | 0:47.0 | OVERHEAD | One hand grabs cluster of puppy chow, lifts up | "the kitchn" end-tag |
| 95 | 0:47.5 | OVERHEAD | Hand exiting top of frame with handful of puppy chow | "the kitchn" end-tag |
| 96 | 0:48.0 | OVERHEAD | Bowl of puppy chow, hands out of frame, static hold | "the kitchn" end-tag logo + text |
| 97 | 0:48.5 | OVERHEAD | Static hero bowl of puppy chow, end-card continues | "the kitchn" end-tag |
| 98 | 0:49.0 | OVERHEAD | Final static bowl of puppy chow, end-card | "the kitchn" end-tag logo + text |

_Total: 98 frames captioned._


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
