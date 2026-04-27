**This is an analysis task — return the vocabulary directly as your response. Do NOT use plan mode, do NOT write to a plan file, do NOT ask for approval. Just output the markdown vocabulary doc.**

You're synthesizing an editorial-intent vocabulary from observations made on 17 of Dan's recipe edits.

## Goal

Produce a small (10-20 entries) vocabulary of recurring **editorial intents**. Each intent is a NAMED reusable decision that Dan's edits make over and over. The vocabulary is the input to a manifest schema — when the agent generates a future recipe edit, it will read intent tags and translate them into the right effects/cuts/grades.

## Method

1. Read ALL 17 sets of OBSERVATIONS below.
2. Find patterns that recur in **2 or more** recipes. Single-recipe quirks don't make the cut (note them as "candidates" only).
3. For each recurring pattern, write a vocabulary entry with:
   - **Name** (short, evocative — e.g. `phrase-binding-adj-transform` or `hands-absent-breath`)
   - **Definition** (1-2 sentences — what the intent IS, in editorial language)
   - **Realization** (1-2 sentences — what effects/cuts/timings encode it in Premiere)
   - **Recipes where it appears** (slug list, with one-phrase context per recipe)
   - **Counter-examples / when NOT to use** (if visible from observations — e.g. "absent in puppy_chow because…")
4. Group entries into ~5-7 categories. **Stop-Motion MUST be its own dedicated category** (not merged with Composition) — it's a distinctive Dan signature that deserves separate vocabulary entries for its sub-modes (no-hands appearance, micro-cut compilation, ingredient-stacking sequences, etc.). **Speed Ramp / Time Manipulation MUST also have entries** (look for `speed_ramp`, `playback_speed`, RAMP markers, or any mention of slow-mo / speed change / time remapping in the OBSERVATIONS).

## Quality bar

- **Specific, not vague.** Bad: "uses zooms." Good: "single animated Position+Scale on an adjustment layer that spans 2-4 consecutive same-angle ingredient beats, drifting/pushing slowly across the cuts."
- **Recipe-cited.** Every entry must list the recipes where it was observed.
- **Realization-grounded.** Each entry must say what the manifest writer would emit (e.g. "Transform on V3 adj-layer; animated Position keyframes from [0.5,0.5] to [0.5,0.55±0.05]; duration spanning N consecutive cuts").
- **No editorial commentary.** This is a reference doc, not analysis prose.

## Output format

```markdown
# Editorial Intents Vocabulary v1

## Category: {name}

### `intent-slug-name`

**Definition:** {1-2 sentences}

**Realization:** {what to emit in the prproj — effect type, track, params, timing}

**Recipes:** `recipe_a` (one-phrase context); `recipe_b` (one-phrase context); …

**Counter-examples / when not:** {if visible}

---
```

End with a **Vocabulary Coverage Audit** section listing:
- Patterns that appeared in only 1 recipe (candidates for next iteration)
- Observations that don't fit any vocabulary entry yet (gaps to investigate)

## Inputs follow



### baked_lobster_tails

- **MOGRT-driven instructional spine.** Every technique step and every sauce ingredient gets a Graphic Parameters card; cuts are timed to the card's life, not vice versa. Card-in/card-out IS the cut rhythm.
- **No adjustment-layer Transforms anywhere in the published 0–55s.** Dan trusts the underlying photography (macro DOF, in-camera moves, hand-action) to do all the motion work. No punch-ins, no kaleidoscopes — this recipe stays "documentary clean."
- **One isolated speed ramp (V2 28.28–30.28).** Single dynamic flourish in the whole edit, placed on the *first* sauce ingredient (butter) to wake the section up after the prep-block exit; the rest of the sauce build rides flat.
- **Animated-path mask used as a take-stitch, not a transition.** The 24.07s V3 Mask with animated Path/Position is hidden craft — bridges two takes of tails-into-water without the viewer noticing a cut.
- **"No-hands hero" pause beats.** 4.55s bare tail, 18.77s three-tail lineup, 50.84s plated row — Dan inserts object-portrait holds with no hand in frame at structural transitions (intro, prep→bake, bake→plate). These function as visual paragraph breaks.
- **Angle grammar is locational, not stylistic.** FRONT 3/4 = cutting-board work, OVERHEAD = vessel work (dish, saucepan), MACRO CLOSE = beauty/end-card. Angle changes mark *where* you are, and the viewer is trained on that mapping by repetition.
- **Micro-staccato cluster as opening punctuation.** The 4.55–5.38s burst (four sub-half-second V2 cuts on the same composition) is used like a snare roll into the first instructional beat — recurring intro device worth flagging.
- **No Lumetri grading at the timeline level visible in this segment.** Color is locked at acquisition; the bright orange "cooked" reveal at 47s+ works because no grade has flattened it.
- **Cut density tracks instruction density.** 5–19s averages ~2s/shot under MOGRTs (one beat per technique); 28–38s holds the same ~1.3s pace under ingredient labels; the plated outro stretches to 2–3s/shot to slow the read.
- **End-card stack is hand-in-frame on three of four shots.** Dan resists pure object photography for the closer — fingertip dip and held-hero-piece keep a person in the frame at the moment of "this is the food."


### basil_pesto

- **Cold open / close are mirrored slow-mo bookends:** 50% speed on the opening pour over plain pasta and on the closing parm shower over finished pasta. The "before pesto" and "after pesto" hero states are both stretched, treating the dish as the bracket on the recipe.
- **Persistent V5 adjustment-layer Lumetri across the entire prep section (3.88–39.50s)** acts as a unifying base grade so per-clip Lumetri can be additive polish rather than corrective. Every per-clip grade is sitting on top of a stabilized look.
- **Two-beat label grammar for ingredients:** OVERHEAD-with-MOGRT to identify, then a FRONT close-up of the action. Used for garlic, pine nuts, basil. When the formula breaks (label on a non-matching carrier shot at 18.14s "Lemon zest" over a pine-nut dump), it's because labels are being stacked faster than dedicated visuals exist.
- **Carrier-shot reuse for label loading:** The same FRONT garlic-chop hold is recycled at 19.19s, 21.40s, 22.23s as a generic "kitchen action" plate to land additional ingredient labels on, without spending new footage. The chop's static-but-kinetic frame is bland enough to let text dominate.
- **A single chop take broken into 5 micro-cuts (11.64–17.06s) to manufacture a percussive chopping rhythm** — each sub-cut gets its own Lumetri grade, suggesting the cuts were treated as independent shots in the timeline despite coming from one source roll.
- **Hand-absent / stop-motion appearance beats mark transitions to "made" status:** the pesto-in-jar with falling drip (28.82s) and the held-jar overhead (29.61s) both pull hands out of frame to shift from "process" to "product." Same logic at the end with the held bowl.
- **Effects-light composition when in-shot motion is already doing the work:** the pine-nut toast (spoon stir), salt pour into chute, pesto pour into jar, tongs toss — none get Transform/zoom/kaleidoscope. Dan only adds adjustment-layer motion when the underlying clip is held; here the cooking action sells itself.
- **Angle rotation around a single static prop (the running food processor at 23.15–26.99s)** to manufacture progress without time-cuts: OVERHEAD-down-tube → FRONT-feed-pour → FRONT-wide-spin. Three rigs on the same machine reads as elapsed activity.
- **No flashy composite effects in this piece** — no Mirror/Replicate, no big Transform punches. The whole edit is carried by cut rhythm, angle pairs, speed ramps, and unified Lumetri. Reserves "hero" energy for slow-mo bookends rather than mid-piece accents.
- **Ingredient labels stop after Parmesan (35.37s)** — once the dish is plated, the label layer drops away and the brand lockup takes its place. Labels = build phase; logo = consumption phase.


### chicken_thighs

- **Ingredient-build grammar is rigid and load-bearing:** locked overhead glass bowl + lower-left MOGRT name + per-ingredient cut + global Lumetri adjustment layer spanning the whole sequence. Any deviation (chicken-as-ingredient at 21.52s, cilantro-as-ingredient at 36.95s) reuses this grammar to slot non-marinade items into the same vocabulary.
- **Speed is per-shot rhythmic seasoning, not transitions:** 50% on hero pours (soy sauce, finished sear), 455% on less-visual beats (sugar dump). The 50/455 pairing inside one continuous build is a signature — Dan picks one shot in a series to dilate and compresses an adjacent one.
- **Stutter-cut micro-bursts replace effects for tactile beats:** the 23.94–24.73s sequence is eight ~0.08s cuts of bag massage with zero adjustment-layer effects. The cut rhythm itself supplies the kinetic energy where another editor might reach for a Transform or kaleidoscope.
- **Animated-mask + Lumetri rig as a bookend device:** the same complex mask rig (Tracker/Path/Position/Scale/Rotation/Anchor) appears at 1.42s (with title) and 38.58s (without title) — same effect rig, different function. Marks the opening hero and the post-cook hero as a matched pair.
- **OVERHEAD = instructional / FRONT = sensory:** clean rule across this edit. Marinade build and finished-plate beats live overhead; grilling, slicing, hand-action live front. Angle change marks chapter, not energy.
- **Global adjustment-layer Lumetri spans the whole cook (V7, 3.88–45.46s) but per-clip Lumetri also fires:** belt-and-suspenders grading — the global layer unifies, the per-clip Lumetri does individual lifts. Notable that Dan keeps both.
- **Speed RAMP (6 keyframes at 19.85–21.52s) used as chapter pivot, not flourish:** it's the seam between marinade and protein, and it's the only true ramp in the edit. Ramps are reserved for structural transitions here, not decoration.
- **No Mirror/Replicate/kaleidoscope, no Transform punch-in adjustment layers in this recipe at all:** Dan let cuts, speed, and grading carry every beat. Worth flagging — if other recipes lean on those effects for similar moments (ingredient build, sear reveal), this one's restraint is a deliberate stylistic choice for a "classic" recipe.
- **Hand-presence pairing is consistent:** opening title plate is hand-in (1.42s) → no-hand (2.59s); ingredient drops are all hand-in; closing slice is hand-in (39.75s) → no-hand fan-out (40.92s). The no-hand "settled" beat after a hand-action beat is the breath.
- **MOGRT is the only sectioning device:** no L-cuts, no fades, no chapter cards. Text overlays do all the labeling work, and the chicken-thighs/refrigerate/cilantro overlays slot into ingredient-list visual grammar to extend it past just marinade ingredients.


### congee

- **Single global Lumetri across the entire cook** (V6 adj 3.34→39.66), bypassing the cold-open title shot — Dan grades the *process* as one continuous tonal block, not per clip.
- **No Transforms, no kaleidoscope, no Mirror/Replicate composites anywhere** — this recipe relies entirely on cut rhythm, in-shot kinetics (sizzle, pours, stream), and labels. Effect-restraint is itself the choice; the cooking does the motion work.
- **Stop-motion ingredient-appearance beats** repeat in two distinct chains (aromatics 12.72–18.06, dry seasonings inside 21.40–27.11) — hands deliberately removed so ingredients seem to materialize. Distinct mood from the hand-pour beats interleaved with them.
- **Repeating-composition rhythm gag**: aromatic chain holds the same tight side framing across three ingredients, swapping only the label. Variation comes from the ingredient itself, not the camera.
- **Angle flips track information needs**: FRONT for streams/pours/single-ingredient drama, OVERHEAD for pot geography and pull-backs that re-orient before a rhythm change.
- **Label re-use as bookend**: "Fresh scallions" and "Toasted sesame oil" appear twice — once in the cook, once at plating — closing a structural loop without the viewer being told it's a callback.
- **One micro-cut burst** (six sub-second splits at 30.61) handles the percussive moment that other recipes might solve with a Transform punch-in. Cut-rhythm substitutes for effect.
- **Speed retime reserved for the final hero** (70% on the closer) — the only time-manipulation in the piece, used as a "stay here" signal at the outro.
- **MOGRT callout (lightbulb tip card) used exactly once**, on the wash beat, where text-on-screen needs a held, in-action background — Dan picks the one shot that can sustain a 3s read.
- **Cold-open hero = closing hero, same composition** — the cut answers itself across 36 seconds, and the 70% retime is what turns the repeat into a payoff rather than a literal repeat.


### crab_ragoon

- **Locked OVERHEAD + V8 label-per-cut as the ingredient-dump grammar.** When ingredients are being added one-by-one to a single bowl, Dan locks the angle, lets the pour/drop motion carry kinetics, and swaps a top-left text label on every cut. No Transforms, no per-clip grades — a single adjustment-layer Lumetri unifies the whole montage.
- **V1↔V2 ping-pong on adjacent ingredient beats.** Alternating which track holds each clip in the dump section — likely a workflow tic for clean handles and easy retiming, not a visual effect. The viewer never sees it; the editor benefits.
- **Per-clip Lumetri on fry/finish, adjustment-layer Lumetri on dump/assembly.** Dan grades by section logic: when the look needs to be uniform across many short cuts (ingredient list), one adjustment layer; when each shot has a unique hero-color need (oil glow, crust amber), per-clip.
- **Sustained instructional callout = sustained shot.** The "Trace the border with a finger dipped in water" graphic spans ~3.3s and three micro-cuts of essentially the same setup — the callout demanding read-time is what justifies the dwell.
- **Hand-absence as section punctuation.** The lined-up tray of unfried parcels (28.74) and the salted-rack overhead (38.29) are stop-motion-style "result" beats with no hands. Both sit between an action montage (folding / frying) and the next phase — Dan uses no-hand result shots as breath marks.
- **Surface/color as section divider.** White marble (mixing) → teal cutting board (assembly) → blue Dutch oven (frying) → white plate (serving). Angle changes alone aren't the divider; the surface change carries the chapter break.
- **Cold-open and outro share FRONT/dipping-bowl framing.** A composition rhyme bookends the piece — the first and final hero shots match each other, not just in subject but in lens/angle.
- **Three-cut sequences for multi-stage actions.** Frying (drop / cook / lift) and folding (corner / pinch / seal) are both decomposed into 3–4 quick cuts rather than one sustained take, even when the underlying clip has its own motion. Compresses real-world dwell time without speed-ramping.
- **Absence of Transforms throughout.** No punch-ins, mirrors, or kaleidoscopes in this edit — every kinetic moment is carried by in-shot motion (pours, hand entries, sizzle, salt fall). When the recipe doesn't need accent, Dan trusts the practical motion.
- **Ingredient-label grammar re-used as instructional grammar.** "Wonton wrappers / Crab mixture" labels in assembly and "Kosher salt" at the rack are the same MOGRT visual language as the bowl-dump section — used to mark "this is the named element of this beat" beyond just the ingredient list.


### cranberry_jalepeno_dip

- **Stop-motion / hand-absent beats are used to punctuate hand-action runs** — empty-bowl-then-scallions-appear (7.76s) and empty-plate-staging (24.86s) sit between kinetic loading shots. These beats have a designed-graphic feel that contrasts with the cooking-process beats around them.
- **Stacked adjustment-layer composite for chapter-break stingers** — at the processor → ingredient-board pivot (9.88–10.18s), an animated Zoom-In Transform on V2 sits atop a 4× Mirror + Replicate kaleidoscope on V1. Either alone would be too decorative or too plain; the combo gives propulsion + visual rupture in 0.3s.
- **Per-clip Lumetri on rapid label runs** — each ingredient-pour clip in the 10.18–17.02s sequence gets its own Lumetri rather than relying solely on the overarching adj-layer grade. Suggests Dan is matching subtle exposure shifts between takes so the locked overhead composition doesn't flicker.
- **Adjustment-layer grade restarts on section boundaries** — the V6/V7 Lumetri stack ends and immediately restarts at 19.48s and 30.28s, aligning with section transitions (processor → mixer, build → finale). Lets each chapter sit in its own color world while staying internally consistent.
- **Effects are absent precisely where the underlying clip is already kinetic** — no Transform on the FRONT macro cold-open (chip pull does it), no Transform on pour shots (cascading powder/liquid does it), no Transform on the FRONT through-glass processor shot (berries jostle). Effects appear only where the static frame would otherwise stall.
- **Speed ramps replace cuts at points where action peaks need to be amplified rather than re-framed** — the 18.52–19.48s pestle-press uses a 6-keyframe ramp instead of a punch-in, letting the hand action itself become the energy beat.
- **Masked Lumetri for surgical correction on uneven lighting** — the 32.66s overhead beauty shot uses a static 4-vertex mask to isolate-grade a region. This is utility-grade work, not a stylistic flourish — when the global grade can't satisfy the whole frame, mask it.
- **Locked composition + per-clip grading is the spine of ingredient-board sections** — Dan stays on a single overhead and lets MOGRT labels + pour kinetics drive the rhythm. Cuts land *on the start of pour action* (anticipation cuts), not on its peak or aftermath.
- **Long holds bookend the piece** — the sub-3s clips dominate the body, but the cold open (~2.5s) and the closing hero pair (~3s each) hold longer. Rhythm asymmetry signals "intro/outro" without overlay treatment.
- **Angle changes serve one of two roles:** (1) reveal something the prior angle couldn't show (FRONT processor shot reveals tumbling depth; spread MACRO reveals dimensional spoon contact), or (2) reset color world for a new section (mixer bowl's blue plastic). They are not cosmetic — each transition adds information or marks structure.


### cucumber_tea

- **Sub-100ms Lumetri-flicker bursts** at three structural moments (cold open, mid-build dump, final-assembly) are Dan's signature for manufacturing energy on inherently slow/static compositions. Same trick reused as both opening hook and act-climax marker — bookending texture.
- **One master V6 adjustment-layer Lumetri spans the entire build act** (3.34–36.45s) while individual V2 clips get their own per-clip Lumetri only at flicker beats. So: master grade for cohesion, per-clip grade exclusively as a rhythmic punctuation device — not for color correction.
- **Zero Transform/Mirror/Replicate effects in this edit.** Energy comes entirely from cut rhythm + Lumetri-flicker — the kaleidoscope/zoom toolkit isn't needed when ingredient labeling does the heavy lifting visually.
- **Locked-frame ingredient list (12.64–19.06s):** identical OVERHEAD-close composition reused for 6+ ingredient adds, varying only the topping and the label. Builds rhythm through repetition, not angle change.
- **Stop-motion hand-absence beat (8.76–10.18s)** sits between the salt-sprinkle action and the drain-time MOGRT — the held no-hands frame is the visual transition from "doing" to "waiting."
- **Boxed graphic MOGRT vs plain ingredient text** is a deliberate semantic distinction — boxed = process/instruction (drain time), plain = ingredient identification. Holds across the edit.
- **Angle logic is task-driven, not stylistic:** OVERHEAD for ingredient identification and pour/dump actions where the surface is the subject; FRONT 3/4 for tools where blade depth or knife travel matters; FRONT close for the final cross-section payoff.
- **Reverse-zoom finale via cuts, not Transform** — three sustained shots descending in scale do the work an effect would do in other edits. Implies Dan trusts the underlying coverage over post-effects when coverage exists.
- **Ingredient label timing follows action peaks:** label appears with the ingredient hitting the pile (dill drop, chive pour, mayo squeeze) — not during a held still. Label reinforces the action moment rather than annotating a static frame.
- **The cold-open hero is graded-flickered, not the plated-FRONT hero that follows.** Two heroes back-to-back, but only the OVERHEAD one gets effect treatment — the FRONT one earns its sustained beat by virtue of having an entering hand and depth. Effect treatment is reserved for compositions that lack in-shot motion.


### flaky_pie_crust

- **Bookend hero loop**: opens and closes on nearly identical OVERHEAD shots of the finished crust on the sheet pan. The opener gets a Mirror+Replicate kaleidoscope and Zoom-In stacked over the title; the closer plays it straight. The "answer the opener" structural rhyme is a signature device.
- **Recipe-wide stacked Lumetri grade (V5 + V6)** runs the entire body (3.34–46.09); two Lumetri instances on V5 (one tagged "Green") plus a third on V6 — i.e., a base grade with a green/cool-cast correction underneath, applied across every clip rather than per-shot.
- **Per-shot Lumetri spikes layered on top of the base grade** for hero/payoff moments only (36.62–37.54 rolling; 44.13–46.09 baked rim macro). Used as accent grading, not corrective.
- **Text labels carry rhythm during single continuous clips**: dry-ingredient sequence (3.34–7.51) is one camera shot, but the V8 label swaps (Flour/Sugar/Salt) act as the perceived cuts. Means the cook can pour-pour-pour without a coverage cut.
- **MOGRT callouts intentionally bridge cuts** to unify two-shot demonstrations — pea-size tip (10.84–13.18) spans a FRONT→OVERHEAD swap so the *tip* feels singular even as the technique shown changes.
- **No-hands "appearance" beats** at deliberate transition points: butter-cube reveal (9.13), bare-floured-marble fleck (31.32). Both function as reset/bridge moments, dropping action so the next phase can start fresh.
- **Slow speed for reverence, speed ramps for rhythm**: 50% on the wrapped-disc (29.03), wrapped-disc-into-fridge implication (29.61); 50% on the hand-out at finished shell (43.04). Multi-keyframe RAMP curves (32.62, 35.20) on the rolling-pin section to add motion phrasing rather than uniform slow-down.
- **OVERHEAD = schematic/spatial; FRONT = sensory/textural** is rigorously enforced. Pours, ingredient placement, and dough-into-pan transfers stay overhead; whisks, crumble, ice-strain, butter-cubes, baked rim get FRONT macro.
- **Ingredient introductions follow a two-beat grammar**: top-down "label shot" (overhead, often with no/minimal action and a text overlay) followed by FRONT kinetic pour/action. Repeats across flour-sugar-salt, butter, and ice water.
- **Effects are absent during inherently kinetic underlying footage** — fork-tossing montage (20.27–22.73), whisk macro (7.51), crumble (13.18). Dan only adds Transform/Mirror/speed effects when the underlying clip is held or the moment needs structural punctuation.


### french_onion_mac_cheese

- **Master Lumetri lives on V3 as a single adjustment layer** spanning the entire recipe body (3.34–61.73s) — Dan grades the recipe as one piece, then layers per-clip Lumetri on V1/V2 only when an individual shot fights the master grade. The V3 master is the floor, per-clip is the patch.
- **Surgical masked grades are reserved for problem white-on-white shots.** The only two masks in the timeline (4.63s and 44.38s) sit on visually difficult cream-pot/cream-sauce frames where a global lift would blow out highlights.
- **No Transform/Mirror/Replicate effects anywhere** in this recipe. Dan uses zero kinetic adjustment-layer composites — the energy comes entirely from cut rhythm + in-shot action (pours, sizzles, whisks, dumps). When the underlying clip is kinetic, no effect is applied; when it's a held "state" beat, it's intentionally held.
- **Signature "no hands / stop-motion" beats** punctuate the piece at structural seams: empty pot opener (3.34s), boiling water (18.52s), reduced onions (24.90s), browned bake reveal (54.89s). These hands-absent shots are Dan's editorial periods between hand-action sentences.
- **Ingredient chips vs. boxed pill MOGRTs are functionally distinct.** Ingredient names (corner chip, no box) label additions; boxed-pill callouts ("Cook undisturbed 5 minutes," "Bake at 475°F") mark wait/time-passage beats. The visual treatment encodes "this is a thing" vs "this is a wait."
- **Mid-clip chip swaps** (e.g., 49.13s "More caramelized onions" appearing during an existing V2 shot) avoid unnecessary cuts on continuous gestures while still annotating both ingredient hits.
- **Same-axis multi-beat sequences** dominate transformation moments — béchamel build (31.41–37.70s) and bowl mixing (14.31–18.52s) are locked overhead so the audience reads texture/color change as continuous rather than chasing a moving camera.
- **The 44.38s static-mask micro-composite** is the only narrative-flag effect in the whole piece — Dan saves the timeline's most distinctive editorial gesture for the conceptual reunion of caramelized onions with the cheese sauce, the dish's identity moment.
- **Cut pace front-loads** — sub-1s cuts in the cold open (0.88–3.34s) versus 2–3s holds in the bake/finish — energy decays as we move from "hook" to "settle."
- **Single 75% speed ramp on the final clip** is the only speed manipulation; Dan doesn't reach for speed ramps as a regular tool, reserving slow-mo strictly for the closing hero beat.


### jiffy_corn_casserole

- **Animated masks are reserved for bookends (open + close), not body shots.** Dan uses Mask2 with keyframed Path/Position/Anchor Point only on the title (1.17–3.80) and the closing hero (38.12–42.58); the middle of the recipe is mask-free. Masks signal "this is a frame, not a step."
- **Stacked adjustment layers gate phase changes.** A second adjustment layer (V7) switches on exactly when raw ingredients become batter (22.77s) and stays on through bake + reveal. The grade-stack is doing chapter punctuation that no cut announces.
- **FRONT for vertical action, OVERHEAD for surface action.** Every pour/drop/scoop where gravity is the story is FRONT (butter cubes, sour cream dollop, corn cascade, final scoop); every assembly/spread on the bowl-or-pan plane is OVERHEAD (microwave step, eggs+sour cream, Jiffy box, pan smoothing).
- **Hand-frame "presentation" beats stand in for off-screen process.** The 5.13s shot frames the bowl with two hands rather than cutting to a microwave — turning a black-box step into a visible recipe beat. The hands present rather than act, giving it a stop-motion-ish flavor.
- **Label-swap on a sustained shot replaces a cut.** The 9.22–14.35s OVERHEAD holds through sour cream → eggs additions; only the text overlay changes. Dan compresses two ingredient beats into one shot when the action stays on the same plate.
- **Macro inserts hide jump-cuts in repeated overheads.** Between two near-identical OVERHEAD stir frames (16.06 and 18.52), a FRONT macro of swirling batter (17.18) absorbs the time jump and adds a texture beat.
- **Title labels delay-fire on multi-beat product shots.** "Jiffy corn muffin mix" appears on the *second* beat of the box-pour, not the first — letting the action establish before the brand reads. Same delay logic on the bake card (caption arrives ~4.7s into a 7s hold).
- **Long holds + delayed captions create the only "breath" in the cut.** The bake plate is 7s — three to five times longer than any other beat. Dan trades pace for anticipation when the recipe itself demands a wait.
- **No Transform/zoom adjustment-layer effects anywhere.** Motion energy comes from in-shot action (pours, falling kernels, whisk, spatula, lifting scoop) and from masked grades on the bookends — never from synthetic punch-ins. The shots are doing the kinetic work.
- **Cold-open and close are intentional mirrors with asymmetric grade work.** Both are the spoon-lifting-hero FRONT close-up; the open carries title + animated mask sweep, the close carries an animated masked spotlight on the lifted bite. The matched composition with different mask intents brackets the piece.


### loaded_baked_potatoes

- **Stutter/strobe V2 sub-clips bookend the bacon thread.** Identical-frame ~0.08s flutter on V2 appears at the first ingredient call (3.34s "Bacon") and again at the topping callback (40.33s, on the bacon-towel shot). Used as a percussive accent under text overlays, not a transition.
- **Kaleidoscope = time-compression signature.** Mirror×4 + Replicate stack on V1 with a Transform Zoom on V3 adj overhead is reserved for the single "while this cooks at length" jump (raw bacon → cooked bacon, 5.42–5.67s). One-shot use; treated as the recipe's hero stylistic flourish.
- **Two-tier Lumetri (body grade vs. finishing grade).** A single Lumetri runs the entire procedural body (3.34–46.38s) and is re-cut to a new instance for the finished-product section (46.38–55.22s). Grade change marks the procedural→presentational pivot, not a creative ramp inside cooking.
- **Speed-ramp grammar: 50% for pours, 75% for the outro lift, 100% for cooking action.** All wet ingredients and the potato dump are 50%; the closing spoon-lift is 75%; stirring/active cooking stays at 100%. Speed encodes "look at this ingredient" vs. "watch this happen."
- **Stop-motion appearance vs. hand-action choice is deliberate per ingredient.** Bacon (raw) appears with no hands; onion is hand-poured (agency required); toppings (cheddar/bacon/chives at the end) all appear with no hands — turning the garnish build into a magic sequence rather than a procedural one.
- **Tight-vs-overhead pairing on liquid adds.** Each pour swaps angle (overhead pot ↔ tight side pour) so every consecutive 50% beat refreshes the composition. Prevents the slo-mo string from feeling like one long shot.
- **No Transform/punch-ins are used over already-kinetic shots.** Stirring, sizzling, dumping, and pouring beats get zero adjustment-layer motion — the in-shot action carries it. Effects are reserved for time-jumps (kaleidoscope) and locked-off composition shots that would otherwise feel inert.
- **Tip-MOGRT has its own visual grammar.** The "mash or blend" callout uses a circular bubble with a lightbulb icon (V9 graphic), distinct from the rectangular ingredient text on V8. The shape change cues "this is advice, not a name."
- **Cold-open hero + outro hero are graded differently from the body.** Title-card hero (1.38–3.34s, pre-Lumetri) and outro beauty (post-46.38s, second Lumetri) flank the singular body grade — the recipe is sandwiched between two presentational color spaces.
- **Bookend pacing: stutter on the in (Bacon flag) and stutter on the callback (bacon topping).** The repeating frame device on V2 is used only twice, both times tied specifically to bacon — making the bacon thread the structural spine of this particular recipe.


### peppermint_bark

- **Effects budget is almost zero.** The whole timeline relies on cuts + angle + MOGRT text. Adjustment-layer Transforms / Mirror / Replicate kaleidoscope effects are *absent*. Dan trusts the in-shot motion (pours, stirs, smashes, slicing) to carry energy.
- **Lumetri grading is reserved for one short stretch (44.67–50.18).** Four consecutive clips receive individual grades — almost certainly a color-match patch across mixed source plates rather than a stylistic mood shift. Notable that grading is *clip-level*, not on an adjustment layer.
- **One single 50% speed ramp (34.24s)** marks the white-chocolate stir as a hero-texture beat — the only timewarp in the cut, used to elevate, not to compress.
- **Two-act parallelism: dark chocolate intro and white chocolate intro are shot and cut identically** (ingredient label → bowl pour → microwave going in → microwave moving → stir → extract pour → stir). The edit teaches the recipe's symmetry.
- **"Found object" / no-hands openings recur** at start of major sections — empty Pyrex bowl (6.30s), empty Ziploc (19.56s), held slab (17.64s). Each functions as a calm reset before the next action burst.
- **OVERHEAD owns the kinetic moments** (pour, smash, spread, sprinkle); FRONT owns the establishing/product beats (microwave, ingredient hero, finished bark). The angle alternation is the rhythm.
- **Cuts compress action; they rarely anticipate or react.** Pours are entered mid-stream, stirs land in the middle of the fold. The edit assumes the viewer reads action instantly.
- **MOGRT instructional cards always sit on top of the *static-feeling* held shots** (microwave-going-in, refrigerate-slab, refrigerate-finished). Action shots stay text-free so motion reads cleanly.
- **V8 carries a persistent overlay (logo bug)** through the entire body 4.71–58.56s with one swap at 54.18s — branding scaffold, not editorial.
- **Bookended hero shots** at 4.71s and 54.18s (both FRONT, both two-hand product holds) frame the video as a complete object rather than a how-to chain.


### pin_wheel

- **Speed-ramp + 50% half-speed sequence as a recipe-list device.** The 5 ingredient pours all share angle, cadence, label position, and 50% speed; ramp out of the block signals "list complete." Pattern repeats on other Kitchn-style edits when an ingredient bullet-list needs to be rendered in motion.
- **Mask-built split-screens for compressed quantitative beats.** The 4-up dough-divide (18.85–19.89s) and the wrapped-dough triptych (~26s) both replace serial cuts with one frame that says "n of these." Reserved for moments where the math of the recipe matters.
- **Stop-motion-flavored "no hands" beats anchor each color step.** Single gel drop on a dough ball with hand only delivering the bottle, not touching the dough — sits between the active mix beats as a clean before-frame. Used twice in matched parallel for red and green.
- **MOGRT label position flips to clear the action.** "Flour mixture" jumps from top-left to top-right specifically because the paddle and red-handled tool entered top-left. Indicates Dan reflows graphics rather than locking corner placement.
- **Hand-built strobe via consecutive 0.08s cuts (no Posterize Time).** The pre-oven sequence is a chain of ~12 micro-cuts of the same V1 source rather than a time effect. Marks a transition rather than ornamenting a beat.
- **Graphic-only filler beats absorb time-jumps.** Two "Refrigerate 1 hour" / "Bake 10 min" cards each get a held base clip + animated Shape/Graphic Parameters stack — the recipe's required waits don't get black frames or stills, they get UI.
- **Per-clip Lumetri stacked on adjustment-layer Lumetri only on hero finals.** The umbrella V9/V10 grade runs the whole show, but the last 3 beauty shots get an additional clip-level Lumetri push for the hero-saturation difference. Reserved for the closing payoff.
- **FRONT angle reserved for two specific functions: hero macros (open and close) and arc-of-motion gestures (flour spray).** Everything mechanical/recipe-instructional is OVERHEAD. The FRONT cuts are deliberate and rare.
- **Cuts land on contact moments, not in anticipation.** Ingredient pours cut at the instant of bowl contact; slice cuts land on the cleaved swirl reveal. Almost no anticipation cuts in this edit.
- **No Transform/Mirror/Replicate/Zoom punch-ins anywhere.** The kaleidoscope/punch-in vocabulary is absent here — the shot's own motion (sizzle/pour/spatula fold/strobe) is doing the energy work. Notable absence given how heavily other Kitchn edits lean on those.


### puppy_chow

- **Locked-overhead "ingredient catalog" with MOGRT labels.** 6.01–11.01s is the signature: same bowl, no camera move, ingredients appear via straight cuts each tagged with a typographic label. Treats the prep as a stop-motion sticker book.
- **No adjustment-layer effects anywhere in this edit.** Zero Transform / Lumetri / Mirror / Replicate. Motion energy comes entirely from in-frame action (chocolate ribboning, bag shaking, color transitions). The shots are doing the work; effects would have been gilding.
- **Color-transformation match cuts.** The stir progression at 15.43–19.69 is a three-cut yellow→marbled→brown sequence on the same lens — Dan trusts the in-frame chemistry to carry the story rather than cutting away.
- **Bookended hero shot.** Same tight side composition opens (with title) and closes (clean) — gives the cut a recognizable frame.
- **Container changes get extra label support.** When the workspace changes (bowl → microwave, bowl → bag, bag → tray), the MOGRTs do double duty as orientation aids ("Cereal mixture" label exists only because the bag is a new vessel).
- **Hand-presence as a deliberate variable.** Ingredient-add beats are mostly *hands-out* (object simply appears); manipulation beats (stirring, microwaving, shaking, dumping) are hands-in. The alternation is rhythmic, not incidental.
- **Microwave gets an unusually long dwell.** Three cuts and a full sentence-long MOGRT for what could have been a single instruction card — the kitsch mint appliance is treated as a personality prop, not just a step.
- **Cut cadence tightens in the shake section.** Six cuts in 6.4 seconds vs. the earlier ~1.5s averages — the percussive run is the only place the edit accelerates noticeably, and it's used precisely where real-life duration is longest.
- **Label cuts run on V9 independent of V1/V2.** Labels live on their own track and time to ingredient cuts, never to the action — letting Dan retime the cut without retiming the type.
- **Side/front shots used for transitions, overhead used for catalog and reveal.** The geography is consistent: overhead = inventory or layout; front/side = action and motion (pour, microwave, shake, hero).


### sauteed_green_beans

- **Stutter clusters as time-compression.** Dan uses 4–5 sub-100ms micro-cuts on the same shot at "waiting" moments (boil at 13.4s, ice-bath cool at 28.9s) to collapse real time without leaving the camera position. Both instances sit at structurally parallel "now we wait" beats.
- **Speed ramps as transition glue.** A 1564% speed clip at 17.43–18.73s replaces what would otherwise be a dissolve between the boil/ice-bath world and the butter-pan world. Speed = transition itself, not an accent.
- **Slow-mo (50%) reserved for the hero gesture.** The only slowdown clip is the green-bean toss at 31.78s — the dish-becoming-the-dish moment. Dan doesn't sprinkle slo-mo around; he banks it for the single most kinetic/visual money shot.
- **Hand-in / hand-out pairing is a structural unit.** Every ingredient stage runs the same three-beat: hand pours → tool stirs → no-hand sizzle/settle. It's how Dan makes overheads feel rhythmic instead of demonstrative.
- **Lumetri timing follows narrative weight.** Per-clip Lumetri only appears once the beans are the hero (35.4s onward). The single sustained adjustment-layer grade — V6 with stacked Green + base Lumetri — covers the entire 13s plating outro, welding final-stage shots into one color world.
- **Bubbling/sizzle as built-in motion engine.** Where most editors would punch in with a Transform, Dan trusts the in-shot kinetics — boiling water, melting butter, frying chips, falling cheese — and leaves the clip clean. No Transform effects appear anywhere in this entire timeline.
- **Macro register breaks from OVERHEAD baseline are reserved for "transformation" moments.** The garlic browning (20.77s), minced garlic sizzle (25.36s), parm rain (37s) — Dan leaves the establishing OVERHEAD to go macro specifically when the *visual change* (color, texture coating) is the story.
- **Setup-then-payoff inserts.** The ice-bath bowl gets pre-established at 10s before it's used at 28.9s — Dan is willing to spend a beat now to make a later cut feel earned rather than abrupt.
- **Title and outro share visual DNA.** Cold-open hero (1.29s) and brand-card hero (51.72s+) are the same FRONT macro register, bookending the cooking sequence — the V6 grade in the outro pulls the closing hero closer to the opening's saturation.
- **No Transform/Mirror/Replicate/Mask in this cut.** The toolbox here is intentionally narrow: cuts, speed, two Lumetri layers, and MOGRT text. Dan's energy work is being done by *editing* (stutter, ramp, register change), not by *effects* (zoom, kaleidoscope). Worth noting if other recipes lean heavily on adjustment-layer Transforms — this one is a counter-example.


### steak_tacos

- **Slow Transform [Position / Scale / Scale Height] on V3 adj layers is Dan's default "add motion across a multi-cut OH ingredient sequence" tool.** It runs across 2–4 cuts at a time (3.88–6.76, 6.76–10.30, 11.43–14.47, 26.86–29.65, 58.60–60.19) and is reserved for sections where the underlying footage is locked-off and the cut count alone wouldn't carry energy.
- **Kaleidoscope (Mirror×4 + Replicate) used exactly once, at the section break.** It fires for ~0.2s with a Transform Zoom-In stacked on top — the only double-adj-layer moment in the timeline. Reserved as the loudest tool, deployed at the single biggest narrative pivot (prep→cook).
- **Stop-motion "ingredient appears" beats alternate with hand-pour beats during the marinade dump.** OJ poured (hand) → lime poured (hand) → garlic scraped (hand) → cilantro just sitting there → salsa just sitting there. The no-hands frames feel like found-object stills and break what would otherwise be repetitive pour-pour-pour rhythm.
- **Reuses identical frames under different labels (salt/pepper at 20.98 vs 22.52).** When two ingredient steps look identical visually, Dan doesn't reshoot — he relabels and lets the MOGRT do the differentiation.
- **OH→FRONT pairs sell "placement → result."** Onions hit grill (OH lay-down → FRONT sizzle); steak hit grill (FRONT lift → OH placement → FRONT sizzle). FRONT for hero/heat, OH for geometry/positioning.
- **Lumetri grades shift by section, not just per-clip.** Cooler/cleaner on prep beats; warmer/redder push during the cook section. The V7 master Lumetri runs the entire 3.88–63.86s spine, with per-clip Lumetri on V1/V2 layered for local correction.
- **Cuts ladder tighter on hero food beats (steak cook 29.65–33.62) instead of using a Transform punch-in.** Real handheld micro-variation across three FRONT takes does the work a digital zoom would fake.
- **Tortilla and gas-flame moments are the only OH framing for non-marinade-bag content.** Reserved for "you can only see this from above" reasons — burner char, ingredient placement on flat pan.
- **Effects are absent during sections where in-shot action is already kinetic** — squishing the bag, slicing the steak, sprinkling toppings, sizzle/smoke shots. Dan trusts the practical motion and only reaches for adj-layer Transform when the underlying frame would otherwise be inert.
- **Title MOGRT bridges across the opening cut.** Rather than pinning the lockup to one shot, it lives over both cold-open clips so the angle change happens under the title — makes the cut feel like part of the title build rather than a hard transition.


### sweet_potato_pie

- **V1=FRONT / V2=OVERHEAD track discipline.** Almost every Lumetri grade lands on V1; OVERHEAD V2 is left ungraded. Treats the eye-level human-presence shots as the place to push warmth and the locked overheads as neutral information.
- **Per-clip Lumetri rather than adjustment-layer grade.** Dan grades individual hero clips (the roasted-potato peel sequence, the spice-stack FRONTs, the pour) rather than blanketing the cut with one LUT — saturation is reserved for emotional beats.
- **Speed ramps on long uneventful overhead actions (rolling, crimping, brown-sugar drop).** 6-keyframe ramps compress real time without the unnatural look of straight speed multipliers.
- **50% slow-mo bookends + pour.** Reserved for the title plate, the flour sprinkle, and the filling pour — three "poster" moments. Slow-mo is a saturation tool here, not a clarity tool.
- **No adjustment-layer composites in this cut.** No Transform punch-ins, no Mirror+Replicate kaleidoscope, no stacked V3/V5 layers. Reads as a "calm classic Kitchn" build — the recipe's warmth is carried by grading and slow-mo, not by graphic flourish.
- **Two-tier MOGRT grammar.** Floating-word labels for ingredients (single-word, no box); boxed callouts for instructions (temperature, time, refrigerate). Different shapes do different jobs.
- **Empty-frame entries.** Several beats begin with an empty surface (cutting board, marble) and the prop slides in — uses in-shot motion as the cut's own animation, no editorial effect needed.
- **OH→FRONT→OH sandwich for processed ingredients.** Repeats at the food-processor section: locked OH establish, kinetic FRONT, locked OH new-state. A reusable mini-grammar for transformations.
- **FRONT shots cluster around hands+tools (fork, knife, spoon, processor); OVERHEAD clusters around clean ingredient drops and finished plates.** Hand presence is the deciding factor for which track a shot lives on.
- **Cuts land on action-peak, not anticipation.** Knife-down, peel-pull, spoon-out, ingredient-impact-with-mixture — Dan's tendency is to land the cut *on* the contact frame rather than before or after.

