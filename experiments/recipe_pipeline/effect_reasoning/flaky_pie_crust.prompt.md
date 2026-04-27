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
| 1.54–1.96s | V2 | ADJ | Transform (Zoom In) [animated: Scale Height] |  |  |
| 1.75–1.96s | V1 |  | Mirror (Main), Mirror (Main), Mirror (Main), Mirror (Main), Replicate (Main) |  |  |
| 1.96–3.34s | V1 |  | — |  |  |
| 3.34–7.51s | V2 |  | — |  |  |
| 3.34–40.87s | V5 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |
| 3.34–46.09s | V6 | ADJ | Lumetri Color |  |  |
| 3.34–42.96s | V7 |  | — |  |  |
| 3.34–4.71s | V8 |  | Text (All-purpose flour) |  |  |
| 4.71–6.17s | V8 |  | Text (Granulated sugar) |  |  |
| 6.17–7.51s | V8 |  | Text (Kosher salt) |  |  |
| 7.51–9.13s | V1 |  | — |  |  |
| 9.13–10.84s | V2 |  | — |  |  |
| 9.13–10.84s | V8 |  | Text (Cold unsalted butter) |  |  |
| 10.84–11.80s | V1 |  | — |  |  |
| 10.84–13.18s | V9 |  | Graphic Parameters | The butter\rshould be\rthe size\rof a pea! |  |
| 11.80–13.18s | V1 |  | — |  |  |
| 13.18–14.22s | V1 |  | — |  |  |
| 14.22–15.47s | V1 |  | — |  |  |
| 14.22–15.47s | V8 |  | Text (Ice water) |  |  |
| 15.47–16.39s | V1 |  | — |  |  |
| 16.39–19.19s | V1 |  | — |  |  |
| 19.19–20.27s | V2 |  | — |  |  |
| 20.27–21.52s | V1 |  | — |  |  |
| 21.52–22.73s | V1 |  | — |  |  |
| 22.73–26.86s | V1 |  | — |  |  |
| 26.86–27.86s | V1 |  | — |  |  |
| 27.86–29.03s | V1 |  | — |  |  |
| 29.03–31.32s | V1 |  | — |  |  |
| 29.61–31.32s | V8 |  | Graphic Parameters | Refrigerate for at least 1 hour |  |
| 31.32–32.62s | V1 |  | — |  |  |
| 32.62–33.70s | V1 |  | — |  |  |
| 32.62–35.20s | V8 |  | Graphic Parameters |  A flour-dusted\rrolling pin\rprevents the\rdough from\rsticking |  |
| 33.70–35.20s | V1 |  | — |  |  |
| 35.20–36.62s | V1 |  | — |  |  |
| 36.62–37.54s | V1 |  | Lumetri Color |  |  |
| 37.54–39.62s | V1 |  | — |  |  |
| 39.62–40.87s | V1 |  | — |  |  |
| 40.87–43.04s | V1 |  | — |  |  |
| 40.87–46.09s | V5 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |
| 42.96–46.09s | V7 |  | — |  |  |
| 43.04–44.13s | V1 |  | — |  |  |
| 44.13–46.09s | V1 |  | Lumetri Color |  |  |

**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**
- **3.34–46.09s**: V6 (Lumetri Color) stacked over V5 (Lumetri Color (Green), Lumetri Color)
- **3.34–46.09s**: V6 (Lumetri Color) stacked over V5 (Lumetri Color (Green), Lumetri Color)

---

### FRAME_ANALYSIS

# Flaky Butter Pie Crust v2 — Pass 1 Shot List

| Frame | Time | Camera | Subject/Action | Notes |
|-------|------|--------|----------------|-------|
| 1 | 0:00.0 | OVERHEAD | Baked pie crust on sheet pan held with oven mitts | Title card "Flaky Pie Crust / the kitchn" |
| 2 | 0:00.5 | OVERHEAD | Baked pie crust, oven mitts lowering tray to counter | Title card persists |
| 3 | 0:01.0 | OVERHEAD | Baked pie crust settled on counter, mitts releasing | Title card persists |
| 4 | 0:01.5 | FRONT | Whip-pan blur transition across golden crust | Motion blur; speed ramp / whip |
| 5 | 0:02.0 | FRONT | Macro push along twisted fluted crust edge | Shallow focus, hero beauty shot |
| 6 | 0:02.5 | FRONT | Macro glide along twisted crust edge continues | Title card persists |
| 7 | 0:03.0 | FRONT | Macro tracks further along twisted crust edge | Title card persists |
| 8 | 0:03.5 | OVERHEAD | Flour dumped from small glass bowl into large bowl | Text "All-purpose flour"; motion blur on pour |
| 9 | 0:04.0 | OVERHEAD | Small bowl tipped to finish emptying flour | Text "All-purpose flour"; pink manicure visible |
| 10 | 0:04.5 | OVERHEAD | Sugar ramekin tilted toward flour mound | Text "Granulated sugar" |
| 11 | 0:05.0 | OVERHEAD | Sugar poured onto flour pile | Text "Granulated sugar"; mid-pour |
| 12 | 0:05.5 | OVERHEAD | Sugar mound sitting atop flour, ramekin pulled away | Text "Granulated sugar" |
| 13 | 0:06.0 | OVERHEAD | Hand holding small salt ramekin enters frame toward flour mound | Text "Kosher salt" |
| 14 | 0:06.5 | OVERHEAD | Salt being tipped onto flour/sugar pile | Text "Kosher salt"; mid-pour |
| 15 | 0:07.0 | OVERHEAD | Hand finishes tap-emptying salt ramekin over mound | Text "Kosher salt" |
| 16 | 0:07.5 | FRONT | Whisk plunging into dry flour mound in bowl | Camera angle shift; macro whisking |
| 17 | 0:08.0 | FRONT | Whisk strokes through flour, starting to level pile | Dry-ingredient whisk beat |
| 18 | 0:08.5 | FRONT | Whisk continues combining dry ingredients | Flour texture evenly distributed |
| 19 | 0:09.0 | FRONT | Butter cubes scattered across surface of flour in bowl | Text "Cold unsalted butter"; shallow focus |
| 20 | 0:09.5 | FRONT | More butter cubes landing on flour, small puff of flour | Text "Cold unsalted butter"; drop motion |
| 21 | 0:10.0 | FRONT | Butter cubes settled in cratered flour bed | Text "Cold unsalted butter" |
| 22 | 0:10.5 | FRONT | Butter cubes held on flour surface (near-still beat) | Text "Cold unsalted butter"; hold |
| 23 | 0:11.0 | FRONT | Hands crumbling/smearing butter into flour | Callout "The butter should be the size of a pea!" with lightbulb icon |
| 24 | 0:11.5 | FRONT | Hands pinching butter and flour between fingers | Callout persists; fingertip technique |
| 25 | 0:12.0 | OVERHEAD | Bench scraper pulled through flour/butter mixture | Callout persists; pastry-cutter style cut-in |
| 26 | 0:12.5 | OVERHEAD | Bench scraper continues cutting butter into flour | Callout persists |
| 27 | 0:13.0 | FRONT | Hand lifts shaggy butter-flour crumble, lets it fall | Texture check; crumbly shreds falling |
| 28 | 0:13.5 | FRONT | Crumbly mixture continues cascading from fingers | Hero texture beauty beat |
| 29 | 0:14.0 | OVERHEAD | Ice water poured from large measuring cup into smaller Pyrex | Text "Ice water"; ice cubes visible |
| 30 | 0:14.5 | OVERHEAD | Water continues filling smaller cup, ice tongs/spoon held | Text "Ice water" |
| 31 | 0:15.0 | OVERHEAD | Pour finishing into ice-filled measure cup | Text "Ice water" |
| 32 | 0:15.5 | FRONT | Empty 1-cup Pyrex in foreground, water streaming in | Pyrex logo prominent; fresh setup |
| 33 | 0:16.0 | FRONT | Water continues streaming into Pyrex measure | Pyrex logo visible |
| 34 | 0:16.5 | FRONT | Hand holds tablespoon over ice-water Pyrex, scooping | Measuring ice water by the spoon |
| 35 | 0:17.0 | FRONT | Full tablespoon of water lifted from Pyrex | Spoon hovers mid-air |
| 36 | 0:17.5 | FRONT | Tablespoon of water moved over empty glass bowl | Transferring water to dry mix |
| 37 | 0:18.0 | FRONT | Tablespoon poised above crumble mixture in bowl | About to pour |
| 38 | 0:18.5 | OVERHEAD | Tablespoon delivering water drops over crumble | Water landing on butter-flour mix |
| 39 | 0:19.0 | OVERHEAD | Measuring cup tilted over crumble, small pour | Small Pyrex measure held at angle |
| 40 | 0:19.5 | OVERHEAD | Pyrex tipped more, continuing to drizzle water | Water pooling on crumble |
| 41 | 0:20.0 | OVERHEAD | Pyrex nearly vertical, finishing the drizzle | Mid-pour |
| 42 | 0:20.5 | FRONT | Fork tossing/tumbling dough crumble in bowl | Shaggy dough forming |
| 43 | 0:21.0 | FRONT | Fork continues tossing, clumps getting larger | Gluten barely forming |
| 44 | 0:21.5 | FRONT | Macro of shaggy dough clumps being turned | Dough just comes together |
| 45 | 0:22.0 | FRONT | More dough tossing, still ragged but cohesive | Texture nearly there |
| 46 | 0:22.5 | OVERHEAD | Mixing bowl tilted to show shaggy dough crumble inside | Hands supporting bowl |
| 47 | 0:23.0 | OVERHEAD | Bowl tilted further, dough mass visible | Showing texture level |
| 48 | 0:23.5 | OVERHEAD | Shaggy dough dumped onto marble counter | Empty bowl edge visible below |
| 49 | 0:24.0 | OVERHEAD | Hand presses scattered crumble on marble to consolidate | Side-hand pressing dough together |
| 50 | 0:24.5 | OVERHEAD | Crumble continues being pressed flat into a shaggy slab | Scooting loose crumbs inward |
| 51 | 0:25.0 | OVERHEAD | Two hands cup dough mass, shaping into first disk | Second pile of crumble on right |
| 52 | 0:25.5 | OVERHEAD | Hands rotate/round first small dough disk | Formed disk visible |
| 53 | 0:26.0 | OVERHEAD | One disk finished (left), hands shaping second disk (right) | Two disks in frame; split dough |
| 54 | 0:26.5 | OVERHEAD | Hands continue pressing and rounding second disk | Both disks in frame |
| 55 | 0:27.0 | FRONT | Hand pats/shapes second disk on marble, first disk visible right | Finger-shaping edges; camera angle shift |
| 56 | 0:27.5 | FRONT | Two finished dough disks resting on marble counter | Beauty resting shot |
| 57 | 0:28.0 | OVERHEAD | One disk wrapped in plastic wrap on left, unwrapped on right | Cling film wrap start |
| 58 | 0:28.5 | OVERHEAD | Hand adjusting plastic wrap around left disk, right disk uncovered | Wrapping in progress |
| 59 | 0:29.0 | FRONT | Hands holding wrapped dough disk up to camera | Disk wrapped tightly in plastic |
| 60 | 0:29.5 | FRONT | Hands lower wrapped disk | Text "Refrigerate for at least 1 hour" lower-third banner |
| 61 | 0:30.0 | FRONT | Wrapped disk moved offscreen, empty marble left | Banner "Refrigerate for at least 1 hour" persists |
| 62 | 0:30.5 | FRONT | Empty marble with title banner, transition beat | Banner persists; scene change |
| 63 | 0:31.0 | FRONT | Empty marble, banner still visible | Banner persists |
| 64 | 0:31.5 | FRONT | Hand places chilled unwrapped dough disk on floured marble | Flour dust visible on counter |
| 65 | 0:32.0 | FRONT | Finger-shaping edges of disk after placement | Prepping for roll-out |
| 66 | 0:32.5 | OVERHEAD | Rolling pin dusted with flour presses down on disk | Callout "A flour-dusted rolling pin prevents the dough from sticking" |
| 67 | 0:33.0 | OVERHEAD | Rolling pin rolls dough outward, disk flattens wider | Callout persists |
| 68 | 0:33.5 | OVERHEAD | Dough rolled into a large thin round | Callout persists |
| 69 | 0:34.0 | OVERHEAD | Rolling pin continues pressing to even out dough sheet | Callout persists |
| 70 | 0:34.5 | OVERHEAD | Final roll-out, dough circle large and thin | Callout persists |
| 71 | 0:35.0 | OVERHEAD | Dough draped/rolled onto rolling pin, pie plate visible above | Transport move; empty glass pie plate positioned |
| 72 | 0:35.5 | OVERHEAD | Dough half-unrolled over glass pie plate | Draping across pie dish |
| 73 | 0:36.0 | OVERHEAD | Rolling pin lifts away, dough settled over pie plate | Ragged overhang on edges |
| 74 | 0:36.5 | OVERHEAD | Hands press dough into pie plate bottom and sides | Shaping shell into plate |
| 75 | 0:37.0 | OVERHEAD | Hand continues pressing and smoothing dough into plate | Shell taking form |
| 76 | 0:37.5 | FRONT | Macro close-up: thumbs pinching/crimping edge | Crimping fluted rim technique |
| 77 | 0:38.0 | FRONT | Hands continue crimping rim around pie shell | Hero detail of flutes forming |
| 78 | 0:38.5 | FRONT | Macro crimping continues, scalloped rim visible | Pattern of flutes around edge |
| 79 | 0:39.0 | FRONT | Macro crimp detail showing defined zigzag edge | Crimp finalized |
| 80 | 0:39.5 | OVERHEAD | Finished raw crust on sheet pan, hands steadying tray | Pre-bake hero; fluted scalloped edge |
| 81 | 0:40.0 | OVERHEAD | Raw crust tray held centered for overhead beauty | Pre-bake hero persists |
| 82 | 0:40.5 | OVERHEAD | Tray drops into frame revealing baked golden crust | Whip transition into bake reveal |
| 83 | 0:41.0 | FRONT | Macro of baked crust edge from side, shallow focus pull | Shallow DOF, toasty fluted rim |
| 84 | 0:41.5 | FRONT | Macro continues along baked golden crimped edge | Beauty shot |
| 85 | 0:42.0 | FRONT | Continued macro glide along fluted baked edge | Shallow DOF |
| 86 | 0:42.5 | FRONT | Camera pushes further along baked crust rim | Beauty shot |
| 87 | 0:43.0 | FRONT | Tilt-up reveals interior of baked shell with docking holes | "the kitchn" end-card logo appears |
| 88 | 0:43.5 | FRONT | Wider view of baked shell interior, rim out of focus | End-card logo with text |
| 89 | 0:44.0 | OVERHEAD | Baked pie shell on sheet pan, full overhead beauty shot | End-card "the kitchn" logo |
| 90 | 0:44.5 | OVERHEAD | Baked shell static, end-card logo persists | End-card logo |
| 91 | 0:45.0 | OVERHEAD | Baked shell continues as end card | End-card logo |
| 92 | 0:45.5 | OVERHEAD | Final frame of baked flaky pie crust | End-card logo |

_Total: 92 frames captioned._


---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
