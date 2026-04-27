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
| 1.17–2.50s | V1 |  | — |  |  |
| 2.50–3.21s | V1 |  | — |  |  |
| 3.21–5.21s | V2 |  | — |  |  |
| 3.21–62.48s | V8 |  | — |  |  |
| 3.21–5.21s | V9 |  | Text (Sweet potatoes) |  |  |
| 5.21–7.30s | V1 |  | — |  |  |
| 7.30–10.05s | V2 |  | — |  |  |
| 8.26–10.05s | V9 |  | Graphic Parameters | Bake at 375°F until tender,\r45 to 60 minutes |  |
| 10.05–11.39s | V1 |  | — |  |  |
| 10.05–11.39s | V9 |  | Text (Flour) |  |  |
| 11.39–12.72s | V1 |  | — |  |  |
| 11.39–12.72s | V9 |  | Text (Pie dough) |  |  |
| 12.72–13.85s | V2 |  | — |  |  |
| 13.85–15.02s | V2 |  | — |  |  |
| 15.02–16.31s | V1 |  | — |  |  |
| 16.31–17.56s | V2 |  | — |  |  |
| 17.56–18.73s | V1 |  | — |  |  |
| 18.73–20.69s | V1 |  | — |  |  |
| 20.69–22.27s | V2 |  | — |  |  |
| 22.27–24.52s | V2 |  | — |  |  |
| 23.02–24.52s | V9 |  | Graphic Parameters | Refrigerate for 30 minutes |  |
| 24.52–25.73s | V1 |  | — |  |  |
| 25.73–27.07s | V1 |  | Lumetri Color |  |  |
| 27.07–28.24s | V1 |  | Lumetri Color |  |  |
| 28.24–29.78s | V1 |  | Lumetri Color |  |  |
| 29.78–30.78s | V2 |  | — |  |  |
| 30.78–32.41s | V1 |  | Lumetri Color |  |  |
| 32.41–33.78s | V2 |  | — |  |  |
| 33.78–35.08s | V2 |  | — |  |  |
| 33.78–35.08s | V9 |  | Text (Eggs) |  |  |
| 35.08–36.54s | V2 |  | — |  |  |
| 35.08–36.54s | V9 |  | Text (Evaporated milk) |  |  |
| 36.54–38.58s | V2 |  | — |  |  |
| 36.54–38.58s | V9 |  | Text (Light brown sugar) |  |  |
| 38.58–40.12s | V2 |  | — |  |  |
| 38.58–40.12s | V9 |  | Text (Vanilla extract) |  |  |
| 40.12–41.37s | V1 |  | Lumetri Color |  |  |
| 40.12–41.37s | V9 |  | Text (Ground cinnamon) |  |  |
| 41.37–42.58s | V1 |  | Lumetri Color |  |  |
| 41.37–42.58s | V9 |  | Text (Ground ginger) |  |  |
| 42.58–43.79s | V1 |  | Lumetri Color |  |  |
| 42.58–43.79s | V9 |  | Text (Ground nutmeg) |  |  |
| 43.79–43.84s | V1 |  | Lumetri Color |  |  |
| 43.79–43.84s | V9 |  | Text (Ground nutmeg) |  |  |
| 43.84–45.13s | V1 |  | Lumetri Color |  |  |
| 43.84–45.13s | V9 |  | Text (Kosher salt) |  |  |
| 45.13–47.13s | V2 |  | — |  |  |
| 47.13–48.34s | V2 |  | — |  |  |
| 48.34–49.80s | V2 |  | — |  |  |
| 49.80–50.93s | V1 |  | Lumetri Color |  |  |
| 50.93–51.76s | V1 |  | Lumetri Color |  |  |
| 51.76–53.80s | V2 |  | — |  |  |
| 52.55–53.80s | V9 |  | Graphic Parameters | Bake until filling is mostly set,\r40 to 60 minutes |  |
| 53.80–55.89s | V2 |  | — |  |  |
| 55.89–57.27s | V1 |  | — |  |  |
| 57.27–58.85s | V2 |  | — |  |  |
| 58.85–61.23s | V1 |  | — |  |  |
| 61.23–62.48s | V1 |  | — |  |  |
| 62.48–66.65s | V1 |  | — |  |  |
| 62.48–66.65s | V8 |  | — |  |  |

---

### FRAME_ANALYSIS

# Sweet Potato Pie v2 — Pass 1 Shot List (Part 1, frames 1-67)

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.0 | OVERHEAD | Hands present finished sweet potato pie in glass dish on marble | Title card text: "Sweet Potato Pie" + "the kitchn" logo |
| 2 | 0:00.5 | OVERHEAD | Hands hold glass pie dish centered, baked pie visible | Title card: "Sweet Potato Pie" + "the kitchn" logo |
| 3 | 0:01.0 | FRONT | Hand places plated pie slice topped with whipped cream on marble, whole pie in BG | Title card: "Sweet Potato Pie" + "the kitchn" logo |
| 4 | 0:01.5 | FRONT | Slice of pie with whipped cream dollop on speckled plate, hand on plate rim | Title card: "Sweet Potato Pie" + "the kitchn" logo |
| 5 | 0:02.0 | FRONT | Slice holds on plate, hand retracting | Title card: "Sweet Potato Pie" + "the kitchn" logo |
| 6 | 0:02.5 | FRONT | Close-up of pie slice, fork with bite of filling in foreground right | Title card: "Sweet Potato Pie" + "the kitchn" logo |
| 7 | 0:03.0 | OVERHEAD | Empty white cutting board on marble | Text overlay: "Sweet potatoes"; logo bottom-right |
| 8 | 0:03.5 | OVERHEAD | Hands arrange four raw sweet potatoes in a row on board | Text overlay: "Sweet potatoes" |
| 9 | 0:04.0 | OVERHEAD | Hands finish arranging four sweet potatoes, pulling back | Text overlay: "Sweet potatoes" |
| 10 | 0:04.5 | OVERHEAD | Four sweet potatoes laid out in row, hands out of frame | Text overlay: "Sweet potatoes" |
| 11 | 0:05.0 | FRONT | Hand pierces sweet potato with fork on cutting board, three potatoes in frame | Logo bottom-right |
| 12 | 0:05.5 | FRONT | Hand continues piercing/poking sweet potato with fork | Logo bottom-right |
| 13 | 0:06.0 | FRONT | Hand retracts from poked potato; fork-pricked holes visible | Logo bottom-right |
| 14 | 0:06.5 | FRONT | Hand returns with fork, poking new row of holes on same potato | Logo bottom-right |
| 15 | 0:07.0 | FRONT | Hand resting atop poked sweet potato after fork pierce | Logo bottom-right |
| 16 | 0:07.5 | OVERHEAD | Hands place foil-lined sheet pan with two pricked sweet potatoes | Logo bottom-right |
| 17 | 0:08.0 | OVERHEAD | Sheet pan sliding/motion blur — potatoes being moved on foil | Motion blur suggests speed ramp or camera slide |
| 18 | 0:08.5 | OVERHEAD | Empty marble surface, cutting board edge visible | Text overlay (MOGRT-style box): "Bake at 375°F until tender, 45 to 60 minutes" |
| 19 | 0:09.0 | OVERHEAD | Empty marble surface, same framing | Text overlay: "Bake at 375°F until tender, 45 to 60 minutes" |
| 20 | 0:09.5 | OVERHEAD | Empty marble surface, same framing | Text overlay: "Bake at 375°F until tender, 45 to 60 minutes" |
| 21 | 0:10.0 | FRONT | Low angle on marble counter with scattered flour on surface | Text overlay: "Flour" |
| 22 | 0:10.5 | FRONT | Flour remains scattered on marble; hand entering top-left | Text overlay: "Flour" |
| 23 | 0:11.0 | FRONT | Flour on marble, wider spread | Text overlay: "Flour" |
| 24 | 0:11.5 | FRONT | Hands plop ball of pie dough onto floured marble | Text overlay: "Pie dough" |
| 25 | 0:12.0 | FRONT | Hands press/shape pie dough disk on floured marble | Text overlay: "Pie dough" |
| 26 | 0:12.5 | OVERHEAD | Pie dough disk centered; hands bring rolling pin up from bottom | Logo bottom-right |
| 27 | 0:13.0 | OVERHEAD | Hands roll wooden rolling pin over dough disk | Logo bottom-right |
| 28 | 0:13.5 | OVERHEAD | Dough rolled into larger round; one hand steadies, pin to right | Logo bottom-right |
| 29 | 0:14.0 | OVERHEAD | Hands continue rolling pin across wider dough round | Logo bottom-right |
| 30 | 0:14.5 | OVERHEAD | Hands roll pin across large thin dough round | Logo bottom-right |
| 31 | 0:15.0 | FRONT | Dough rolled onto pin being carried over empty Pyrex pie dish | Logo bottom-right |
| 32 | 0:15.5 | FRONT | Dough unrolling off pin into glass pie dish | Logo bottom-right |
| 33 | 0:16.0 | FRONT | Dough draped into glass pie dish, rolling pin removed | Logo bottom-right |
| 34 | 0:16.5 | OVERHEAD | Hands press dough down into pie dish, excess hangs over edge | Logo bottom-right |
| 35 | 0:17.0 | OVERHEAD | Both hands smoothing dough against sides of dish | Logo bottom-right |
| 36 | 0:17.5 | FRONT | Hands fit dough into pie dish interior, crimping edges | Logo bottom-right |
| 37 | 0:18.0 | FRONT | Hands continue pressing dough against dish interior | Logo bottom-right |
| 38 | 0:18.5 | FRONT | Hands pinching/rolling rim edge with index/thumb | Logo bottom-right |
| 39 | 0:19.0 | FRONT | Continued rim tucking — both hands working rim edge | Logo bottom-right |
| 40 | 0:19.5 | FRONT | Two hands crimping dough rim of pie shell | Logo bottom-right |
| 41 | 0:20.0 | OVERHEAD | Hands crimping fluted rim pattern around pie shell | Logo bottom-right |
| 42 | 0:20.5 | OVERHEAD | Fluted/scalloped rim progressing around dough pie shell | Logo bottom-right |
| 43 | 0:21.0 | OVERHEAD | Hands crimping rim, half of rim shows scallop pattern | Logo bottom-right |
| 44 | 0:21.5 | OVERHEAD | More scallops formed around rim, hands continuing | Logo bottom-right |
| 45 | 0:22.0 | OVERHEAD | Nearly full scalloped rim, hands finishing final flutes | Logo bottom-right |
| 46 | 0:22.5 | OVERHEAD | Finished scalloped pie shell, hands holding dish at sides | Logo bottom-right |
| 47 | 0:23.0 | OVERHEAD | Empty marble surface | Text overlay (MOGRT-style box): "Refrigerate for 30 minutes" |
| 48 | 0:23.5 | OVERHEAD | Empty marble surface | Text overlay: "Refrigerate for 30 minutes" |
| 49 | 0:24.0 | OVERHEAD | Empty marble surface | Text overlay: "Refrigerate for 30 minutes" |
| 50 | 0:24.5 | FRONT | Sheet pan of roasted sweet potatoes slides into frame from above-right | Caramelized juices on foil |
| 51 | 0:25.0 | FRONT | Four roasted sweet potatoes in sheet pan, caramel-glossy, oven mitt visible top-left | Logo bottom-right |
| 52 | 0:25.5 | FRONT | Hand with paring knife scoring length of top sweet potato to split skin | Logo bottom-right |
| 53 | 0:26.0 | FRONT | Knife continues slicing along top of baked sweet potato | Logo bottom-right |
| 54 | 0:26.5 | FRONT | Knife cuts open sweet potato revealing orange flesh, food processor bowl BG-left | Logo bottom-right |
| 55 | 0:27.0 | FRONT | Hands peel/open skin of sweet potato, exposing orange flesh | Logo bottom-right |
| 56 | 0:27.5 | FRONT | Hand holds opened sweet potato; knife scrapes flesh toward food processor | Logo bottom-right |
| 57 | 0:28.0 | FRONT | Close-up: spoon scraping orange flesh from sweet potato skin over food processor bowl | Logo bottom-right |
| 58 | 0:28.5 | FRONT | Hands continue scooping flesh with spoon over food processor | Logo bottom-right |
| 59 | 0:29.0 | FRONT | Larger chunk of sweet potato flesh being scooped out with spoon | Logo bottom-right |
| 60 | 0:29.5 | FRONT | Scoop of orange flesh falling off spoon into food processor bowl | Logo bottom-right |
| 61 | 0:30.0 | OVERHEAD | Food processor bowl filled with scooped sweet potato flesh chunks | Logo bottom-right |
| 62 | 0:30.5 | OVERHEAD | Same framing, slight tonal/composition shift — flesh settled in bowl | Possible speed ramp hold |
| 63 | 0:31.0 | FRONT | Side view of food processor running — sweet potato chunks blurring against wall | Motion blur = food processor running |
| 64 | 0:31.5 | FRONT | Food processor running, flesh forming smoother puree at bottom | Motion blur |
| 65 | 0:32.0 | FRONT | Food processor with puree forming, smoother consistency | Motion blur, running |
| 66 | 0:32.5 | OVERHEAD | Finished smooth orange puree in food processor bowl, spatula visible right | Logo bottom-right |
| 67 | 0:33.0 | OVERHEAD | Smooth orange sweet potato puree, spatula entering from bottom-left | Logo bottom-right |
| 68 | 33.5 | OVERHEAD | Smooth sweet potato puree in food processor bowl, white spatula scraping side | metal blade visible |
| 69 | 34.0 | OVERHEAD | Two whole egg yolks dropped onto puree, third pouring in from measuring cup at right | text overlay: "Eggs" |
| 70 | 34.5 | OVERHEAD | Four egg yolks now visible arranged around central blade | text overlay: "Eggs" |
| 71 | 35.0 | OVERHEAD | Five egg yolks around blade, evaporated milk beginning to pour from lower right | text overlay: "Evaporated milk" |
| 72 | 35.5 | OVERHEAD | Evaporated milk pouring in larger stream, spreading across puree surface | text overlay: "Evaporated milk" |
| 73 | 36.0 | OVERHEAD | Milk fully pooled covering right half, eggs visible top and left | text overlay: "Evaporated milk" |
| 74 | 36.5 | OVERHEAD | Scoop of light brown sugar added over eggs and milk mixture | text overlay: "Light brown sugar" |
| 75 | 37.0 | OVERHEAD | Brown sugar scoop being tipped in, crumbling onto surface | text overlay: "Light brown sugar"; slight zoom/crop change |
| 76 | 37.5 | OVERHEAD | Brown sugar mound larger, sugar crumbles spreading | text overlay: "Light brown sugar" |
| 77 | 38.0 | OVERHEAD | Brown sugar further dispersed, milk more evenly distributed | text overlay: "Light brown sugar" |
| 78 | 38.5 | OVERHEAD | Vanilla extract pouring from glass measuring cup on right | text overlay: "Vanilla extract" |
| 79 | 39.0 | OVERHEAD | Vanilla pooled on right side forming dark amber puddle | text overlay: "Vanilla extract" |
| 80 | 39.5 | OVERHEAD | Hand reaching in from right (red nails) to scrape/mix, vanilla visible lower right | text overlay: "Vanilla extract" |
| 81 | 40.0 | OVERHEAD | Close-up: amber swirl of puree on left, cream on right, sugar dome center with egg yolks right | text overlay: "Ground cinnamon"; tighter framing |
| 82 | 40.5 | OVERHEAD | Cinnamon pouring from small glass jar onto center of mixture, hand with red nails on jar | text overlay: "Ground cinnamon" |
| 83 | 41.0 | OVERHEAD | Cinnamon mound forming on top of orange/cream boundary, jar lifting away | text overlay: "Ground cinnamon" |
| 84 | 41.5 | OVERHEAD | Ground ginger added beside cinnamon mound forming pale yellow pile | text overlay: "Ground ginger" |
| 85 | 42.0 | OVERHEAD | Ginger pile settled alongside cinnamon, composition stable | text overlay: "Ground ginger" |
| 86 | 42.5 | OVERHEAD | Jar of nutmeg hovering above in upper left, spice piles in view | text overlay: "Ground nutmeg" |
| 87 | 43.0 | OVERHEAD | Nutmeg jar lowering, no powder yet falling, spice mound composition | text overlay: "Ground nutmeg" |
| 88 | 43.5 | OVERHEAD | Nutmeg added — darker flecks on top of cinnamon | text overlay: "Ground nutmeg" |
| 89 | 44.0 | OVERHEAD | White kosher salt sprinkling down from pinched fingers above | text overlay: "Kosher salt"; tighter crop |
| 90 | 44.5 | OVERHEAD | Salt pile now visible on top of ginger/cinnamon area | text overlay: "Kosher salt" |
| 91 | 45.0 | OVERHEAD | Extreme close-up POV down feed tube of food processor, contents blurring/spinning | motion blur — processor running |
| 92 | 45.5 | OVERHEAD | Down-the-feed-tube POV: pale cream/yellow ingredients partially blended at bottom | processor running |
| 93 | 46.0 | OVERHEAD | Feed tube POV: contents spinning into orange/amber streaks, motion-blurred | processor running; color shifting |
| 94 | 46.5 | OVERHEAD | Feed tube POV: smoother homogenous yellow-orange liquid spinning | filling coming together |
| 95 | 47.0 | FRONT | Blurry close-up of food processor pour spout tilted, red-nailed hand lifting lid — transition frame | heavy motion blur; speed ramp likely |
| 96 | 47.5 | OVERHEAD | Pull back to full food processor bowl filled with smooth bright orange filling, blade dotted with batter | mixing complete |
| 97 | 48.0 | OVERHEAD | Static hold on smooth filling in processor bowl, fewer bubbles, surface settling | still/hold beat |
| 98 | 48.5 | OVERHEAD | Empty crimped pie crust in glass dish on sheet pan, two hands (orange nails) gripping sides | marble countertop; crust ready |
| 99 | 49.0 | OVERHEAD | Same empty crust, hands repositioning/holding dish | static composition |
| 100 | 49.5 | OVERHEAD | Same empty crust framing, hands steady at right edge | near-identical to prior — hold |
| 101 | 50.0 | FRONT | Side angle: orange filling pouring in thin stream from processor bowl into empty crust | first pour |
| 102 | 50.5 | FRONT | Filling pour continuing, small pool forming in bottom center of crust | pour in progress |
| 103 | 51.0 | FRONT | Pour continuing, filling now covers bottom half of crust | |
| 104 | 51.5 | FRONT | Crust now nearly full, filling pouring into larger pool, fills approaching rim | |
| 105 | 52.0 | OVERHEAD | Pull up to overhead: full filled pie on sheet pan, bracketed by oven-mitt-covered hands at bottom | transition into oven insert suggestion |
| 106 | 52.5 | OVERHEAD | Marble countertop with text card appearing center screen, baking sheet edge visible at bottom | text overlay card: "Bake until filling is mostly set, 40 to 60 minutes" |
| 107 | 53.0 | OVERHEAD | Same text card on marble, baking sheet no longer visible | text overlay card: "Bake until filling is mostly set, 40 to 60 minutes" |
| 108 | 53.5 | OVERHEAD | Same text card, plain marble background | text overlay card held |
| 109 | 54.0 | FRONT | Close overhead-angled view of baked pie: deep golden-orange filling, golden crimped crust, set surface | baked pie reveal |
| 110 | 54.5 | OVERHEAD | Pull back: full baked pie on sheet pan flanked by oven mitts (brown dotted) at frame edges | mitts at edges |
| 111 | 55.0 | OVERHEAD | Same baked pie on sheet pan, slight reframe/zoom closer | tighter crop |
| 112 | 55.5 | OVERHEAD | Baked pie centered on sheet, mitts still bracketing | near-identical hold |
| 113 | 56.0 | FRONT | Pie server lifting first slice out of whole pie on marble counter — clean cut profile visible | hero slice lift |
| 114 | 56.5 | FRONT | Slice raised higher on server, clearer profile of filling against crust | |
| 115 | 57.0 | FRONT | Slice lifted even higher, hand visible at upper left holding server | |
| 116 | 57.5 | OVERHEAD | Plated slice on speckled stoneware plate with whipped cream dollop, pie dish partly visible at left | hero plate, split composition |
| 117 | 58.0 | OVERHEAD | Same plated slice, small reframe, red-nail hand at right edge of plate | hold |
| 118 | 58.5 | OVERHEAD | Same plated slice, hand withdrawn | settled hero |
| 119 | 59.0 | FRONT | Close low-angle of plated slice: fork descending toward cream dollop at upper left | fork entering frame |
| 120 | 59.5 | FRONT | Fork resting on slice near dollop, tines beginning to press into filling edge | |
| 121 | 60.0 | FRONT | Fork tines piercing into side of slice, pulling first bite off | fork cutting through |
| 122 | 60.5 | FRONT | Fork lifting small chunk of filling away from slice, gap forming in side | bite broken off |
| 123 | 61.0 | FRONT | Very tight macro on slice corner with dollop — creamy filling texture visible, fork gone | macro beauty |
| 124 | 61.5 | FRONT | Same macro composition, slight reframe | macro hold |
| 125 | 62.0 | FRONT | Same macro, minimal change | macro hold |
| 126 | 62.5 | FRONT | Pull back to slice on speckled plate with whipped cream + Kitchn logo/text appearing top right | "the kitchn" end card text appearing |
| 127 | 63.0 | FRONT | Same hero slice, Kitchn logo + "the kitchn" text fully visible top right | end card held |
| 128 | 63.5 | FRONT | Hero slice with logo, minor reframe, bite-off chunk visible bottom right | end card |
| 129 | 64.0 | FRONT | Nearly identical hero hold with "the kitchn" logo top right | end card |
| 130 | 64.5 | FRONT | Same framing, stoneware plate with crumb at bottom right | end card |
| 131 | 65.0 | FRONT | Same hero slice, logo still visible top right | end card |
| 132 | 65.5 | FRONT | Tighter crop on slice: bite chunk at bottom foreground, logo still top-right | end card, punched-in |
| 133 | 66.0 | FRONT | Final hero slice frame, logo top-right, bite chunk foreground | end card final |


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
