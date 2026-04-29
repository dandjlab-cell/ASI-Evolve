// Transcript API Probe — discover what's actually reachable from a UXP panel.
//
// Strategy: don't assume the API shape from docs. Try to call every transcript-
// and graphics-related symbol I extracted from the Premiere binary, and log
// what's accessible vs. what throws.

const ppro = require("premierepro");

const $ = (id) => document.getElementById(id);
const log = (...args) => {
  const line = args.map(stringify).join(" ");
  const wrap = $("log-wrap");
  const wasAtBottom = (wrap.scrollHeight - wrap.scrollTop - wrap.clientHeight) < 30;
  $("log").appendChild(document.createTextNode(line + "\n"));
  if (wasAtBottom) wrap.scrollTop = wrap.scrollHeight;
  console.log(...args);
};

function stringify(v) {
  if (v === undefined) return "undefined";
  if (v === null) return "null";
  if (typeof v === "function") return `[function ${v.name || "anon"}]`;
  if (typeof v === "object") {
    try { return JSON.stringify(v, null, 2); } catch { return Object.prototype.toString.call(v); }
  }
  return String(v);
}

function listKeys(obj, prefix = "") {
  if (!obj || typeof obj !== "object") {
    log(`${prefix} (not an object: ${typeof obj})`);
    return;
  }
  const own = Object.getOwnPropertyNames(obj).sort();
  const proto = Object.getPrototypeOf(obj);
  const protoOwn = proto ? Object.getOwnPropertyNames(proto).filter(k => k !== "constructor").sort() : [];
  log(`${prefix} own (${own.length}):`, own.join(", "));
  if (protoOwn.length) log(`${prefix} proto (${protoOwn.length}):`, protoOwn.join(", "));
}

function tryCall(label, fn) {
  try {
    const result = fn();
    log(`✓ ${label}`, "→", typeof result === "object" ? Object.prototype.toString.call(result) : String(result));
    return result;
  } catch (e) {
    log(`✗ ${label}`, "→", `THREW: ${e.message || e}`);
    return undefined;
  }
}

// ─── 1. Probe top-level namespace ────────────────────────────────────────────
$("probe-namespace")?.addEventListener("click", () => {
  log("─── Top-level ppro namespace ───");
  log("typeof ppro:", typeof ppro);
  listKeys(ppro, "ppro.");

  log("\n─── Constants ───");
  if (ppro.Constants) {
    listKeys(ppro.Constants, "ppro.Constants.");
    for (const k of Object.keys(ppro.Constants)) {
      const v = ppro.Constants[k];
      if (v && typeof v === "object") {
        log(`  ppro.Constants.${k}:`, Object.keys(v).join(", "));
      }
    }
  } else {
    log("ppro.Constants is", ppro.Constants);
  }
});

// ─── 2. Probe active project ─────────────────────────────────────────────────
let _project = null;
$("probe-project")?.addEventListener("click", async () => {
  log("\n─── Active Project ───");
  try {
    _project = await ppro.Project.getActiveProject();
    log("project:", Object.prototype.toString.call(_project));
    listKeys(_project, "project.");
    if (_project) {
      const proto = Object.getPrototypeOf(_project);
      log("project methods on prototype:", Object.getOwnPropertyNames(proto).filter(k => typeof proto[k] === "function").sort().join(", "));
    }
  } catch (e) {
    log("getActiveProject threw:", e.message);
  }
});

// ─── 3. Probe active sequence ────────────────────────────────────────────────
let _sequence = null;
$("probe-sequence")?.addEventListener("click", async () => {
  log("\n─── Active Sequence ───");
  if (!_project) _project = await ppro.Project.getActiveProject();
  try {
    _sequence = await _project.getActiveSequence();
    log("sequence:", Object.prototype.toString.call(_sequence));
    listKeys(_sequence, "sequence.");
    if (_sequence) {
      const proto = Object.getPrototypeOf(_sequence);
      log("sequence methods on prototype:", Object.getOwnPropertyNames(proto).filter(k => typeof proto[k] === "function").sort().join(", "));
    }
  } catch (e) {
    log("getActiveSequence threw:", e.message);
  }
});

// ─── 4. Probe TRANSCRIPT-related API ────────────────────────────────────────
$("probe-transcript")?.addEventListener("click", async () => {
  log("\n─── Transcript API probe ───");
  if (!_project) _project = await ppro.Project.getActiveProject();
  if (!_sequence) _sequence = await _project.getActiveSequence();

  // Top-level functions
  const transcriptNames = [
    "getTranscriptClip", "getSequenceTextSegments", "getTrackTextSegments",
    "createEmptyTranscriptClip", "createEmptyTextSegments",
    "createAddTranscriptClipFromTextSegmentAction", "createSetTextSegmentsAction",
    "addNewTextSegment", "splitTextSegment", "mergeTextSegments", "removeTextSegment",
    "setSpeakerID", "getWordCountForType",
    "getSelectedTextSegmentIndexesForSequence", "setSelectedTextSegmentIndexesForSequence",
    "getSelectedTextSegmentIndexesForTrack", "setSelectedTextSegmentIndexesForTrack",
    "determineCaptionTrackSettingsFromTranscriptClips",
  ];

  log("\n→ Probing on ppro:");
  for (const name of transcriptNames) {
    log(`  ppro.${name}:`, typeof ppro[name]);
  }

  log("\n→ Probing on Project:");
  for (const name of transcriptNames) {
    if (_project) log(`  project.${name}:`, typeof _project[name]);
  }

  log("\n→ Probing on Sequence:");
  for (const name of transcriptNames) {
    if (_sequence) log(`  sequence.${name}:`, typeof _sequence[name]);
  }

  // Search every namespace under ppro for transcript-named members
  log("\n→ Deep search: any ppro.* member matching /transcript|textseg/i");
  for (const k of Object.keys(ppro)) {
    const v = ppro[k];
    if (v && typeof v === "object") {
      for (const sub of Object.getOwnPropertyNames(v)) {
        if (/transcript|textseg/i.test(sub)) {
          log(`  ppro.${k}.${sub} (${typeof v[sub]})`);
        }
      }
    }
  }

  // Try calling getTranscriptClip if it exists somewhere
  log("\n→ Attempting getTranscriptClip via known paths");
  const candidates = [
    () => ppro.getTranscriptClip?.(),
    () => _project?.getTranscriptClip?.(),
    () => _sequence?.getTranscriptClip?.(),
    () => ppro.TranscriptClip?.getActive?.(),
    () => ppro.Transcript?.getForActiveProject?.(),
  ];
  for (const fn of candidates) {
    tryCall(fn.toString().slice(0, 80), fn);
  }
});

// ─── 5. Probe GRAPHICS API (createGraphicWithTextLayer) ─────────────────────
$("probe-graphics")?.addEventListener("click", async () => {
  log("\n─── Graphics API probe ───");
  if (!_project) _project = await ppro.Project.getActiveProject();
  if (!_sequence) _sequence = await _project.getActiveSequence();

  const graphicsNames = [
    "createGraphicWithTextLayer", "setText", "addTextBlock",
    "createGraphicLayerAction", "createInsertItemAction",
  ];

  log("\n→ Probing on ppro:");
  for (const name of graphicsNames) log(`  ppro.${name}:`, typeof ppro[name]);

  log("\n→ Probing on Sequence:");
  for (const name of graphicsNames) if (_sequence) log(`  sequence.${name}:`, typeof _sequence[name]);

  log("\n→ Deep search: any ppro.* member matching /graphic|text/i");
  for (const k of Object.keys(ppro)) {
    const v = ppro[k];
    if (v && typeof v === "object") {
      for (const sub of Object.getOwnPropertyNames(v)) {
        if (/graphic|text/i.test(sub) && sub !== "addEventListener") {
          log(`  ppro.${k}.${sub} (${typeof v[sub]})`);
        }
      }
    }
  }
});

// ─── 6. Subscribe to every documented event + try transcript event names ────
$("probe-events")?.addEventListener("click", async () => {
  log("\n─── Event subscription probe ───");
  if (!_project) _project = await ppro.Project.getActiveProject();
  if (!_sequence) _sequence = await _project.getActiveSequence();

  if (!ppro.EventManager) {
    log("ppro.EventManager not found. Available:", Object.keys(ppro).filter(k => /event/i.test(k)).join(", ") || "<none>");
    return;
  }

  log("EventManager methods:", Object.getOwnPropertyNames(Object.getPrototypeOf(ppro.EventManager) || ppro.EventManager).join(", "));
  log("Constants enums:", Object.keys(ppro.Constants || {}).join(", "));

  // Subscribe to all known event constants on Project + Sequence
  const subscribe = (target, eventName, label) => {
    try {
      ppro.EventManager.addEventListener(target, eventName, (evt) => {
        const ts = new Date().toISOString().slice(11, 23);
        log(`[${ts}] EVENT ${label} → ${stringify(evt)}`);
      }, false);
      log(`✓ subscribed ${label}`);
    } catch (e) {
      log(`✗ subscribe ${label}: ${e.message}`);
    }
  };

  for (const enumName of ["ProjectEvent", "SequenceEvent", "VideoTrackEvent", "AudioTrackEvent", "OperationCompleteEvent"]) {
    const en = ppro.Constants?.[enumName];
    if (!en) continue;
    for (const evtName of Object.keys(en)) {
      const target = enumName.startsWith("Project") ? _project : _sequence;
      subscribe(target, en[evtName], `${enumName}.${evtName}`);
    }
  }

  // Try undocumented transcript events
  for (const guess of [
    "TextSegmentsEditedEvent", "TranscriptClipChangedEvent",
    "MasterClipTranscriptClipChangedEvent", "TextSegmentsStructureChangedEvent",
    "transcriptClipChanged", "textSegmentsEdited",
    "TEXT_SEGMENTS_EDITED", "TRANSCRIPT_CLIP_CHANGED",
  ]) {
    subscribe(_sequence, guess, `(guess) ${guess}`);
    subscribe(_project, guess, `(guess on project) ${guess}`);
  }

  if (typeof ppro.EventManager.addGlobalEventListener === "function") {
    for (const guess of ["TextSegmentsEditedEvent", "TranscriptClipChangedEvent"]) {
      try {
        ppro.EventManager.addGlobalEventListener(guess, (evt) => {
          log(`[GLOBAL] ${guess} → ${stringify(evt)}`);
        });
        log(`✓ global subscribed (guess) ${guess}`);
      } catch (e) {
        log(`✗ global ${guess}: ${e.message}`);
      }
    }
  }

  log("\nNow edit the transcript in Premiere — any fired events will log here.");
});

// ─── Utilities ──────────────────────────────────────────────────────────────
// ─── 7. DEEP probe of Transcript / TextSegments / CaptionTrack classes ─────
$("probe-classes-deep")?.addEventListener("click", async () => {
  log("\n─── Deep class probe ───");
  for (const className of ["Transcript", "TextSegments", "CaptionTrack", "SequenceEditor", "SequenceUtils", "Marker", "Markers"]) {
    const cls = ppro[className];
    if (!cls) { log(`✗ ppro.${className} not found`); continue; }
    log(`\n→ ppro.${className} (typeof: ${typeof cls})`);
    // Static members on the class itself
    const staticOwn = Object.getOwnPropertyNames(cls).filter(k => !["length", "name", "prototype"].includes(k));
    log(`  static own (${staticOwn.length}):`, staticOwn.join(", ") || "<none>");
    // Instance methods on the prototype
    if (cls.prototype) {
      const proto = Object.getOwnPropertyNames(cls.prototype).filter(k => k !== "constructor");
      log(`  prototype methods (${proto.length}):`, proto.join(", ") || "<none>");
    }
    // Try common static factory patterns
    for (const factoryName of ["getActive", "getForActiveProject", "create", "createEmpty", "fromMasterClip", "forSequence"]) {
      if (typeof cls[factoryName] === "function") {
        log(`  HAS factory: ${className}.${factoryName}() exists`);
      }
    }
  }
});

// ─── 8. Read sequence's CaptionTrack ────────────────────────────────────────
$("probe-caption-track")?.addEventListener("click", async () => {
  log("\n─── CaptionTrack contents ───");
  if (!_project) _project = await ppro.Project.getActiveProject();
  if (!_sequence) _sequence = await _project.getActiveSequence();

  try {
    const count = typeof _sequence.getCaptionTrackCount === "function" ? await _sequence.getCaptionTrackCount() : "<no method>";
    log(`getCaptionTrackCount: ${count}`);
  } catch (e) { log(`getCaptionTrackCount threw: ${e.message}`); }

  for (let i = 0; i < 5; i++) {
    try {
      const ct = await _sequence.getCaptionTrack(i);
      if (!ct) { log(`getCaptionTrack(${i}) → null/undefined`); continue; }
      log(`\ngetCaptionTrack(${i}) → ${Object.prototype.toString.call(ct)}`);
      log(`  own keys:`, Object.getOwnPropertyNames(ct).join(", ") || "<none>");
      const proto = Object.getPrototypeOf(ct);
      if (proto) log(`  proto methods:`, Object.getOwnPropertyNames(proto).filter(k => k !== "constructor").join(", "));
      // Try common readers
      for (const m of ["getName", "name", "getCaptions", "getItems", "getTrackItems", "getCaptionCount", "isEmpty"]) {
        if (typeof ct[m] === "function") {
          try {
            const r = await ct[m]();
            log(`  ${m}() → ${stringify(r).slice(0, 200)}`);
          } catch (e) { log(`  ${m}() threw: ${e.message}`); }
        } else if (m in ct) {
          log(`  .${m}: ${stringify(ct[m])}`);
        }
      }
    } catch (e) {
      log(`getCaptionTrack(${i}) threw: ${e.message}`);
      break;
    }
  }
});

// ─── 9. Subscribe to DIRTY (known-good) and watch for ANY firings ──────────
$("probe-dirty")?.addEventListener("click", async () => {
  log("\n─── DIRTY listener (known-good event) ───");
  if (!_project) _project = await ppro.Project.getActiveProject();
  let count = 0;
  try {
    _project.addEventListener(ppro.Constants.ProjectEvent.DIRTY, (evt) => {
      count++;
      const ts = new Date().toISOString().slice(11, 23);
      log(`[${ts}] DIRTY #${count} → ${stringify(evt).slice(0, 200)}`);
    });
    log("✓ subscribed to ProjectEvent.DIRTY");
    log("Now go to Premiere and edit the transcript. Every DIRTY fire will log here.");
    log("If DIRTY fires per-keystroke during transcript editing → we have live event coverage.");
    log("If DIRTY only fires on Cmd+S → events are coarser-grained.");
  } catch (e) {
    log(`Subscribe failed: ${e.message}`);
  }
});

// ─── 10. Read transcript via Transcript.exportToJSON ───────────────────────
let _lastTranscriptJSON = null;
$("export-transcript")?.addEventListener("click", async () => {
  log("\n─── Transcript.exportToJSON() ───");
  if (!_project) _project = await ppro.Project.getActiveProject();
  if (!_sequence) _sequence = await _project.getActiveSequence();

  // Try every shape we can think of for exportToJSON's signature
  const attempts = [
    ["no-args",            () => ppro.Transcript.exportToJSON()],
    ["with sequence",      () => ppro.Transcript.exportToJSON(_sequence)],
    ["with project",       () => ppro.Transcript.exportToJSON(_project)],
    ["with project+seq",   () => ppro.Transcript.exportToJSON(_project, _sequence)],
  ];
  for (const [label, fn] of attempts) {
    try {
      const r = await fn();
      log(`✓ ${label} returned (${typeof r}, length=${r?.length ?? "?"})`);
      if (typeof r === "string" && r.length > 0) {
        _lastTranscriptJSON = r;
        log(`First 800 chars:\n${r.slice(0, 800)}`);
        if (r.length > 800) log(`...[+${r.length - 800} more chars]`);
        // Try to parse + count words
        try {
          const parsed = JSON.parse(r);
          log(`Parsed JSON top-level keys: ${Object.keys(parsed).join(", ")}`);
          const blob = JSON.stringify(parsed);
          const wordCount = (blob.match(/"text":/g) || []).length;
          log(`Approx word count (occurrences of "text":): ${wordCount}`);
        } catch (e) {
          log(`Could not JSON.parse: ${e.message}`);
        }
        break;
      }
    } catch (e) {
      log(`✗ ${label} threw: ${e.message}`);
    }
  }
  if (!_lastTranscriptJSON) log("No exportToJSON variant returned data.");
});

// ─── 11. Drop test markers on sequence — proves WRITE path ─────────────────
$("drop-markers")?.addEventListener("click", async () => {
  log("\n▶ START Drop test markers (5 hardcoded)");
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();

    // Hardcoded test "words" — 5 markers at 1s, 2s, 3s, 4s, 5s
    const words = [
      { t: 1.0, text: "hello" },
      { t: 2.0, text: "world" },
      { t: 3.0, text: "this" },
      { t: 4.0, text: "is" },
      { t: 5.0, text: "karaoke" },
    ];

    // Step A: get the Markers collection. Try every plausible accessor.
    log("\n→ Probing Markers accessors:");
    const markersCandidates = [
      ["ppro.Markers.getMarkers(_sequence)",  () => ppro.Markers.getMarkers(_sequence)],
      ["_sequence.getMarkers()",              () => _sequence.getMarkers?.()],
      ["_sequence.markers",                   () => _sequence.markers],
      ["ppro.Markers.getMarkers(_project)",   () => ppro.Markers.getMarkers(_project)],
    ];
    let markers = null;
    let foundLabel = null;
    for (const [label, fn] of markersCandidates) {
      try {
        const r = await fn();
        const tag = Object.prototype.toString.call(r);
        log(`  ${label} → ${tag} (${typeof r})`);
        if (r && (typeof r.createAddMarkerAction === "function" || typeof r.getMarkers === "function")) {
          markers = r;
          foundLabel = label;
          break;
        }
      } catch (e) { log(`  ${label} threw: ${e.message}`); }
    }
    if (!markers) {
      log("✗ No Markers handle. Aborting.");
      log(`■ DONE (no markers handle)`);
      return;
    }
    log(`✓ using ${foundLabel}`);
    log(`  markers methods: ${Object.getOwnPropertyNames(Object.getPrototypeOf(markers)).filter(k => k !== "constructor").join(", ")}`);

    // Step B: build a proper TickTime via the documented static
    log("\n→ Building TickTime via ppro.TickTime.createWithSeconds(1.0):");
    const tt = ppro.TickTime.createWithSeconds(1.0);
    log(`  result: ${Object.prototype.toString.call(tt)} (${typeof tt})`);
    if (tt && typeof tt.seconds !== "undefined") log(`  tt.seconds = ${typeof tt.seconds === "function" ? await tt.seconds() : tt.seconds}`);
    if (tt && typeof tt.ticks !== "undefined") log(`  tt.ticks = ${typeof tt.ticks === "function" ? await tt.ticks() : tt.ticks}`);

    // Inspect Marker class for static factories
    log(`\n→ ppro.Marker statics: ${Object.getOwnPropertyNames(ppro.Marker).filter(k => !["arguments","caller","length","name","prototype"].includes(k)).join(", ")}`);
    log(`  ppro.Marker.prototype: ${Object.getOwnPropertyNames(ppro.Marker.prototype).filter(k => k !== "constructor").join(", ")}`);

    // Step C: build the action with the CORRECT signature
    // createAddMarkerAction(Name, markerType?, startTime?, duration?, comments?)
    log("\n→ createAddMarkerAction with correct (Name, type, startTime, duration, comments) signature:");
    log(`  Marker.MARKER_TYPE_COMMENT = ${ppro.Marker.MARKER_TYPE_COMMENT}`);
    const zero = ppro.TickTime.TIME_ZERO;

    let success = 0;
    let dumpedCompoundMethods = false;
    for (const w of words) {
      try {
        // Build action AND add to compoundAction INSIDE the transaction callback
        const ok = await _project.executeTransaction((compoundAction) => {
          if (!dumpedCompoundMethods) {
            const proto = Object.getPrototypeOf(compoundAction);
            log(`  compoundAction is ${Object.prototype.toString.call(compoundAction)}`);
            log(`  compoundAction methods: ${Object.getOwnPropertyNames(proto).filter(k => k !== "constructor").join(", ")}`);
            dumpedCompoundMethods = true;
          }
          const startTT = ppro.TickTime.createWithSeconds(w.t);
          const action = markers.createAddMarkerAction(
            w.text,
            ppro.Marker.MARKER_TYPE_COMMENT,
            startTT,
            zero,
            ""
          );
          if (!action) throw new Error("createAddMarkerAction returned null");
          // Try the right method on CompoundAction
          if (typeof compoundAction.addAction === "function") compoundAction.addAction(action);
          else if (typeof compoundAction.add === "function") compoundAction.add(action);
          else if (typeof compoundAction.append === "function") compoundAction.append(action);
          else if (typeof compoundAction.push === "function") compoundAction.push(action);
          else throw new Error("no add-method on CompoundAction");
        }, `Add karaoke marker: ${w.text}`);
        log(`  "${w.text}" @ ${w.t}s → executeTransaction returned ${ok}`);
        if (ok) success++;
      } catch (e) {
        log(`  "${w.text}" failed: ${e.message}`);
      }
    }

    log(`\n■ DONE — added ${success}/${words.length} markers. Check the timeline ruler around 1-5s.`);
  } catch (e) {
    log(`■ DONE (with error): ${e.message}\n${e.stack || ""}`);
  }
});

// ─── 12. Navigate sequence → audio track → master clip → transcript ────────
let _masterClip = null;
let _textSegments = null;
$("find-master-clip")?.addEventListener("click", async () => {
  log("\n▶ START Walk to master clip + transcript");
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();

    // Step 1: enumerate audio tracks
    const audioCount = await _sequence.getAudioTrackCount();
    log(`audio track count: ${audioCount}`);

  for (let trackIdx = 0; trackIdx < audioCount; trackIdx++) {
    const track = await _sequence.getAudioTrack(trackIdx);
    if (!track) continue;
    const proto = Object.getPrototypeOf(track);
    const trackMethods = Object.getOwnPropertyNames(proto).filter(k => k !== "constructor");
    log(`\nA${trackIdx + 1} → ${Object.prototype.toString.call(track)}`);
    log(`  methods: ${trackMethods.join(", ")}`);

    // getTrackItems(trackItemType, includeEmptyTrackItems) — both args required
    let items = [];
    try {
      items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
      log(`  getTrackItems(CLIP, false) → array of ${items.length}`);
    } catch (e) {
      log(`  getTrackItems(CLIP, false) threw: ${e.message}`);
    }
    if (!items || !items.length) {
      log(`  no clip items on A${trackIdx + 1}`);
      continue;
    }

    // Inspect first item
    if (items && items.length) {
      const item = items[0];
      const ipproto = Object.getPrototypeOf(item);
      const itemMethods = Object.getOwnPropertyNames(ipproto).filter(k => k !== "constructor");
      log(`  item[0] → ${Object.prototype.toString.call(item)}`);
      log(`    methods: ${itemMethods.join(", ")}`);

      // Try to get the master clip / project item
      for (const m of ["getProjectItem", "projectItem", "getMasterClip", "masterClip"]) {
        if (typeof item[m] === "function") {
          try {
            const pi = await item[m]();
            log(`    ${m}() → ${Object.prototype.toString.call(pi)}`);
            if (pi) {
              _masterClip = pi;
              const piproto = Object.getPrototypeOf(pi);
              const piMethods = Object.getOwnPropertyNames(piproto).filter(k => k !== "constructor");
              log(`    masterClip methods: ${piMethods.join(", ")}`);

              // Try transcript-related methods on the master clip
              for (const tm of ["getTranscript", "transcript", "getTextSegments", "textSegments", "getTranscriptClip"]) {
                if (typeof pi[tm] === "function") {
                  try {
                    const t = await pi[tm]();
                    log(`    pi.${tm}() → ${Object.prototype.toString.call(t)}`);
                    if (t) _textSegments = t;
                  } catch (e) { log(`    pi.${tm}() threw: ${e.message}`); }
                } else if (tm in pi) {
                  log(`    pi.${tm} = ${Object.prototype.toString.call(pi[tm])}`);
                }
              }
              break;
            }
          } catch (e) { log(`    ${m}() threw: ${e.message}`); }
        }
      }
    }
  }

  // Now retry Transcript.exportToJSON with the master clip
  if (_masterClip) {
    log("\n→ Retrying Transcript.exportToJSON with master clip:");
    const variants = [
      ["Transcript.exportToJSON(masterClip)", () => ppro.Transcript.exportToJSON(_masterClip)],
      ["TextSegments.exportToJSON(masterClip)", () => ppro.TextSegments.exportToJSON(_masterClip)],
    ];
    for (const [label, fn] of variants) {
      try {
        const r = await fn();
        log(`  ${label} → ${typeof r} length=${r?.length ?? "?"}`);
        if (typeof r === "string" && r.length > 0) {
          _lastTranscriptJSON = r;
          log(`  First 600 chars:\n${r.slice(0, 600)}`);
        }
      } catch (e) { log(`  ${label} threw: ${e.message}`); }
    }
  }

  // If we got TextSegments, try exporting from it
  if (_textSegments) {
    log("\n→ TextSegments instance methods:");
    const tsproto = Object.getPrototypeOf(_textSegments);
    log(`  ${Object.getOwnPropertyNames(tsproto).filter(k => k !== "constructor").join(", ")}`);
    for (const variant of [
      ["TextSegments.exportToJSON(_textSegments)", () => ppro.TextSegments.exportToJSON(_textSegments)],
      ["Transcript.exportToJSON(_textSegments)",   () => ppro.Transcript.exportToJSON(_textSegments)],
      ["_textSegments.exportToJSON()",             () => _textSegments.exportToJSON?.()],
    ]) {
      const [label, fn] = variant;
      try {
        const r = await fn();
        log(`  ${label} → ${typeof r} length=${r?.length ?? "?"}`);
        if (typeof r === "string" && r.length > 0) {
          _lastTranscriptJSON = r;
          log(`  First 600 chars:\n${r.slice(0, 600)}`);
        }
      } catch (e) { log(`  ${label} threw: ${e.message}`); }
    }
  }

  log(`\n■ DONE  masterClip=${!!_masterClip}  textSegments=${!!_textSegments}  transcriptJSON=${!!_lastTranscriptJSON}`);
  } catch (e) {
    log(`■ DONE (with error): ${e.message}\n${e.stack || ""}`);
  }
});

// ─── 13. Auto-regen loop: subscribe to DIRTY, refresh markers on every fire ──
const KARAOKE_TEST_WORDS = [
  { t: 1.0, text: "hello" },
  { t: 2.0, text: "world" },
  { t: 3.0, text: "this" },
  { t: 4.0, text: "is" },
  { t: 5.0, text: "karaoke" },
  { t: 6.0, text: "loop" },
  { t: 7.0, text: "live" },
];

// Words used by the auto-regen loop. Defaults to test words; replaced when
// real transcript JSON is loaded via Button 15.
let _activeWords = KARAOKE_TEST_WORDS;

let _loopHandler = null;
let _inOurWrite = false;     // guard to ignore DIRTY events caused by us
let _pendingRegen = false;   // debounce: collapse multiple DIRTYs into one
let _lastRegenAt = 0;
const REGEN_DEBOUNCE_MS = 800;

async function clearKaraokeMarkers() {
  const project = await ppro.Project.getActiveProject();
  const sequence = await project.getActiveSequence();
  const markers = await ppro.Markers.getMarkers(sequence);
  let existing = [];
  try { existing = await markers.getMarkers([]); } catch (_) { existing = []; }
  if (!existing || existing.length === 0) return 0;
  await project.executeTransaction((compoundAction) => {
    for (const m of existing) {
      try { compoundAction.addAction(markers.createRemoveMarkerAction(m)); } catch (_) {}
    }
  }, "Clear karaoke markers");
  return existing.length;
}

async function dropKaraokeMarkers(words) {
  const project = await ppro.Project.getActiveProject();
  const sequence = await project.getActiveSequence();
  const markers = await ppro.Markers.getMarkers(sequence);
  await project.executeTransaction((compoundAction) => {
    for (const w of words) {
      const tt = ppro.TickTime.createWithSeconds(w.t);
      const action = markers.createAddMarkerAction(
        w.text,
        ppro.Marker.MARKER_TYPE_COMMENT,
        tt,
        ppro.TickTime.TIME_ZERO,
        ""
      );
      compoundAction.addAction(action);
    }
  }, "Drop karaoke markers");
}

// If true, regenerateKaraoke re-reads /tmp/karaoke_words.json on every fire.
// Toggled on by Button 15 ("Load real transcript").
let _autoReloadJson = false;
const KARAOKE_JSON_PATH = "/tmp/karaoke_words.json";

function readKaraokeJson() {
  const fs = require("fs");
  const raw = fs.readFileSync(KARAOKE_JSON_PATH, "utf8");
  const data = JSON.parse(raw);
  const arr = Array.isArray(data) ? data : (data.words || data);
  if (!Array.isArray(arr)) throw new Error("not an array");
  return arr.map(w => ({
    t: Number(w.t ?? w.start ?? w.start_time ?? 0),
    text: String(w.text ?? w.word ?? "?")
  })).filter(w => w.t >= 0 && w.text);
}

async function regenerateKaraoke(words) {
  // If auto-reload is on, re-read the JSON every regen so we always have the freshest words
  let useWords = words;
  if (_autoReloadJson) {
    try {
      useWords = readKaraokeJson();
      _activeWords = useWords; // remember for next time
    } catch (e) {
      log(`  (auto-reload failed, using cached words): ${e.message}`);
      useWords = words;
    }
  }
  // Set guard so DIRTY events from our own writes don't trigger another regen
  _inOurWrite = true;
  try {
    const cleared = await clearKaraokeMarkers();
    await dropKaraokeMarkers(useWords);
    const sample = useWords.slice(0, 3).map(w => `"${w.text}"@${w.t}s`).join(", ");
    log(`  regen → cleared ${cleared}, added ${useWords.length}  [${sample}${useWords.length > 3 ? "…" : ""}]`);
  } finally {
    // Keep the guard up briefly to swallow any trailing DIRTY events from the writes
    setTimeout(() => { _inOurWrite = false; }, 500);
  }
  _lastRegenAt = Date.now();
}

$("start-loop")?.addEventListener("click", async () => {
  log("\n▶ START auto-regen loop");
  if (_loopHandler) {
    log("  already running");
    return;
  }
  if (!_project) _project = await ppro.Project.getActiveProject();

  _loopHandler = () => {
    if (_inOurWrite) return; // ignore our own writes
    if (_pendingRegen) return; // already scheduled
    _pendingRegen = true;
    setTimeout(async () => {
      _pendingRegen = false;
      const ts = new Date().toISOString().slice(11, 23);
      log(`[${ts}] DIRTY → regenerating ${_activeWords.length} words (debounced)`);
      try { await regenerateKaraoke(_activeWords); }
      catch (e) { log(`  regen failed: ${e.message}`); }
    }, REGEN_DEBOUNCE_MS);
  };
  _project.addEventListener(ppro.Constants.ProjectEvent.DIRTY, _loopHandler);
  log(`✓ subscribed to DIRTY (debounced ${REGEN_DEBOUNCE_MS}ms, self-write guard on)`);
  log("Now do anything that changes the project (Cmd+S, cut, move).");
  log(`Doing initial render now (using ${_activeWords.length} words):`);
  await regenerateKaraoke(_activeWords);
});

$("stop-loop")?.addEventListener("click", async () => {
  if (!_loopHandler) { log("\n(loop not running)"); return; }
  if (!_project) _project = await ppro.Project.getActiveProject();
  try {
    _project.removeEventListener(ppro.Constants.ProjectEvent.DIRTY, _loopHandler);
  } catch (e) { log(`removeEventListener threw: ${e.message}`); }
  _loopHandler = null;
  log("\n⏸ stopped");
});

$("clear-markers")?.addEventListener("click", async () => {
  log("\n→ clearing all markers");
  try {
    const n = await clearKaraokeMarkers();
    log(`  cleared ${n} markers`);
  } catch (e) {
    log(`  clear failed: ${e.message}`);
  }
});

// ─── 19. SAFE: probe Keyframe object shape on Opacity (no Source Text) ─────
// Per-step write to /tmp/uxp_probe.log so we can recover state if anything crashes.
function flushLog() {
  try {
    const fs = require("fs");
    fs.writeFileSync("/tmp/uxp_probe.log", $("log").textContent);
  } catch (_) { /* ignore */ }
}

$("probe-keyframe-shape")?.addEventListener("click", async () => {
  log("\n▶ START Keyframe shape probe (Opacity, scalar — safe)");
  flushLog();
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();

    const track = await _sequence.getVideoTrack(0);
    const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
    if (!items?.length) {
      log("✗ No clips on V1. Add any video clip and re-run."); flushLog(); return;
    }
    const clip = items[0];
    log(`✓ clip: "${await clip.getName()}"`); flushLog();

    const chain = await clip.getComponentChain();
    const compCount = await chain.getComponentCount();
    let opacityComp = null;
    for (let i = 0; i < compCount; i++) {
      const c = await chain.getComponentAtIndex(i);
      if (await c.getDisplayName() === "Opacity") { opacityComp = c; break; }
    }
    if (!opacityComp) { log("✗ no Opacity component"); flushLog(); return; }
    log("✓ found Opacity component"); flushLog();

    // Get param[0] — the actual Opacity scalar
    const opacityParam = await opacityComp.getParam(0);
    log(`✓ Opacity.param[0] displayName="${opacityParam.displayName}"`); flushLog();

    // Read current value via getStartValue — should be safe for Opacity (returns a number-wrapper)
    let current = null;
    try {
      current = await opacityParam.getStartValue();
      log(`✓ getStartValue() → ${Object.prototype.toString.call(current)}`);
      if (current) {
        const proto = Object.getPrototypeOf(current);
        const methods = Object.getOwnPropertyNames(proto).filter(k => k !== "constructor");
        log(`  methods: ${methods.join(", ")}`);
        // Try common accessors
        for (const acc of ["value", "getValue", "asNumber", "toNumber", "number"]) {
          try {
            if (typeof current[acc] === 'function') {
              const r = await current[acc]();
              log(`  .${acc}() → ${typeof r} ${r}`);
            } else if (acc in current) {
              log(`  .${acc} = ${typeof current[acc]} ${current[acc]}`);
            }
          } catch (_) {}
        }
      }
    } catch (e) { log(`  getStartValue threw: ${e.message}`); }
    flushLog();

    // PROBE THE KEYFRAME CONSTRUCTOR — DON'T pass to createSetValueAction yet
    log("\n→ Probing param.createKeyframe(...) signatures (Opacity, no actual write yet):");
    const kfTries = [
      ["createKeyframe()",        () => opacityParam.createKeyframe()],
      ["createKeyframe(50)",      () => opacityParam.createKeyframe(50)],
      ["createKeyframe(50.0)",    () => opacityParam.createKeyframe(50.0)],
    ];
    let workingKeyframe = null;
    for (const [label, fn] of kfTries) {
      try {
        const kf = fn();
        log(`  ${label} → ${Object.prototype.toString.call(kf)}`);
        if (kf) {
          workingKeyframe = kf;
          const proto = Object.getPrototypeOf(kf);
          const methods = Object.getOwnPropertyNames(proto).filter(k => k !== "constructor");
          log(`    keyframe methods: ${methods.join(", ")}`);
          // Show every property on the keyframe
          const ownProps = Object.getOwnPropertyNames(kf);
          log(`    keyframe own props: ${ownProps.join(", ") || "<none>"}`);
          break;
        }
      } catch (e) {
        log(`  ${label} → threw: ${e.message?.slice(0, 80)}`);
      }
      flushLog();
    }

    if (!workingKeyframe) {
      log("\n■ DONE — no createKeyframe variant returned an object. Need different probe."); flushLog(); return;
    }

    log("\n→ NOT calling createSetValueAction this round.");
    log("Once we know the Keyframe shape, the next button will safely write Opacity to test the chain.");
    log("\n■ DONE");
    flushLog();
  } catch (e) {
    log(`■ DONE (with error): ${e.message}`); flushLog();
  }
});

// ─── 20. READ-ONLY probe of Source Text keyframe ──────────────────────────
$("probe-text-keyframe-read")?.addEventListener("click", async () => {
  log("\n▶ START Source Text READ-ONLY probe (no writes, no crash risk)");
  flushLog();
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();
    const track = await _sequence.getVideoTrack(0);
    const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
    if (!items?.length) { log("✗ No V1 clips."); flushLog(); return; }
    const clip = items[0];
    const chain = await clip.getComponentChain();
    let textComp = null;
    for (let i = 0; i < await chain.getComponentCount(); i++) {
      const c = await chain.getComponentAtIndex(i);
      if (await c.getDisplayName() === "Text") { textComp = c; break; }
    }
    if (!textComp) { log("✗ No Text component"); flushLog(); return; }
    const sourceText = await textComp.getParam(0);
    log(`✓ Source Text param obtained`); flushLog();

    // Probe whether keyframes are supported / on
    try { log(`  areKeyframesSupported() = ${await sourceText.areKeyframesSupported()}`); } catch (e) { log(`  areKeyframesSupported threw: ${e.message}`); }
    try { log(`  isTimeVarying() = ${await sourceText.isTimeVarying()}`); } catch (e) { log(`  isTimeVarying threw: ${e.message}`); }
    flushLog();

    // Try getStartValue (returns a Keyframe)
    log("\n→ getStartValue():");
    try {
      const kf = await sourceText.getStartValue();
      log(`  result: ${Object.prototype.toString.call(kf)}`);
      if (kf) {
        log(`  position: ${kf.position ? Object.prototype.toString.call(kf.position) : kf.position}`);
        const v = kf.value;
        log(`  .value: ${Object.prototype.toString.call(v)}`);
        if (v && typeof v === "object") {
          const proto = Object.getPrototypeOf(v);
          const methods = Object.getOwnPropertyNames(proto).filter(k => k !== "constructor");
          log(`    .value methods: ${methods.join(", ") || "<none>"}`);
          const ownProps = Object.getOwnPropertyNames(v);
          log(`    .value own props: ${ownProps.join(", ") || "<none>"}`);
          // Try common accessors
          for (const acc of ["text", "getText", "string", "getString", "data", "getData", "toString", "toJSON"]) {
            try {
              if (typeof v[acc] === "function") {
                const r = await v[acc]();
                const preview = typeof r === "string" ? JSON.stringify(r).slice(0, 80) : Object.prototype.toString.call(r);
                log(`    .value.${acc}() → ${preview}`);
              } else if (acc in v) {
                log(`    .value.${acc} = ${typeof v[acc]} ${typeof v[acc] === 'string' ? JSON.stringify(v[acc]).slice(0, 80) : ''}`);
              }
            } catch (_) {}
          }
        }
      }
    } catch (e) { log(`  threw: ${e.message}`); }
    flushLog();

    // Also try getValueAtTime
    log("\n→ getValueAtTime(TIME_ZERO):");
    try {
      const kf = await sourceText.getValueAtTime(ppro.TickTime.TIME_ZERO);
      log(`  result: ${Object.prototype.toString.call(kf)}`);
      if (kf?.value) log(`  .value: ${Object.prototype.toString.call(kf.value)}`);
    } catch (e) { log(`  threw: ${e.message}`); }
    flushLog();

    log(`\n■ DONE — read only, no writes attempted.`);
    flushLog();
  } catch (e) {
    log(`■ DONE (with error): ${e.message}`); flushLog();
  }
});

// ─── 21. ★ Write Opacity = 50 — single safe write to verify the chain ─────
$("write-opacity-test")?.addEventListener("click", async () => {
  log("\n▶ Write Opacity = 50 (single safe write)");
  flushLog();
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();
    const track = await _sequence.getVideoTrack(0);
    const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
    if (!items?.length) { log("✗ No V1 clips."); flushLog(); return; }
    const clip = items[0];
    const chain = await clip.getComponentChain();
    let opacityComp = null;
    for (let i = 0; i < await chain.getComponentCount(); i++) {
      const c = await chain.getComponentAtIndex(i);
      if (await c.getDisplayName() === "Opacity") { opacityComp = c; break; }
    }
    if (!opacityComp) { log("✗ No Opacity component"); flushLog(); return; }
    const opacityParam = await opacityComp.getParam(0);
    log("✓ Opacity param ready"); flushLog();

    log("→ creating keyframe with value=50"); flushLog();
    const kf = opacityParam.createKeyframe(50);
    log(`  keyframe: ${Object.prototype.toString.call(kf)}`); flushLog();

    log("→ creating setValue action"); flushLog();
    const action = opacityParam.createSetValueAction(kf);
    log(`  action: ${Object.prototype.toString.call(action)}`); flushLog();

    log("→ executing transaction"); flushLog();
    const ok = await _project.executeTransaction((ca) => {
      ca.addAction(action);
    }, "Set Opacity to 50");
    log(`  executeTransaction → ${ok}`); flushLog();
    log(`  ★ Look at the V1 clip in the Program monitor — should be 50% opaque now.`);
    log(`■ DONE`);
    flushLog();
  } catch (e) {
    log(`■ DONE (error): ${e.message}`); flushLog();
  }
});

// ─── 22. Enable time-varying on Source Text and re-read ────────────────────
$("enable-text-tv")?.addEventListener("click", async () => {
  log("\n▶ Enable time-varying on Source Text + re-read");
  log("(Just toggling the keyframe-stopwatch flag. No value writes. Should NOT crash.)");
  flushLog();
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();
    const track = await _sequence.getVideoTrack(0);
    const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
    if (!items?.length) { log("✗ No V1 clips."); flushLog(); return; }
    const clip = items[0];
    const chain = await clip.getComponentChain();
    let textComp = null;
    for (let i = 0; i < await chain.getComponentCount(); i++) {
      const c = await chain.getComponentAtIndex(i);
      if (await c.getDisplayName() === "Text") { textComp = c; break; }
    }
    if (!textComp) { log("✗ no Text component"); flushLog(); return; }
    const sourceText = await textComp.getParam(0);
    log("✓ Source Text obtained"); flushLog();

    log(`  before: areKeyframesSupported=${await sourceText.areKeyframesSupported()}, isTimeVarying=${await sourceText.isTimeVarying()}`);
    flushLog();

    log("→ creating SetTimeVaryingAction(true)"); flushLog();
    const action = sourceText.createSetTimeVaryingAction(true);
    log(`  action: ${Object.prototype.toString.call(action)}`); flushLog();

    log("→ executing transaction"); flushLog();
    const ok = await _project.executeTransaction((ca) => ca.addAction(action), "Enable Source Text keyframing");
    log(`  executeTransaction → ${ok}`); flushLog();

    log(`  after:  areKeyframesSupported=${await sourceText.areKeyframesSupported()}, isTimeVarying=${await sourceText.isTimeVarying()}`); flushLog();

    log("\n→ Re-read getStartValue() / getValueAtTime():");
    try {
      const kf = await sourceText.getStartValue();
      log(`  getStartValue() → ${Object.prototype.toString.call(kf)}`);
      if (kf) {
        const v = kf.value;
        log(`  .value: ${Object.prototype.toString.call(v)}`);
        if (v && typeof v === "object") {
          const proto = Object.getPrototypeOf(v);
          const methods = Object.getOwnPropertyNames(proto).filter(k => k !== "constructor");
          log(`    methods: ${methods.join(", ")}`);
          for (const acc of ["text", "getText", "string", "getString", "data", "toString", "toJSON"]) {
            try {
              if (typeof v[acc] === "function") {
                const r = await v[acc]();
                log(`    .${acc}() → ${typeof r === "string" ? JSON.stringify(r).slice(0, 100) : Object.prototype.toString.call(r)}`);
              } else if (acc in v) {
                log(`    .${acc} = ${typeof v[acc] === "string" ? JSON.stringify(v[acc]).slice(0, 100) : v[acc]}`);
              }
            } catch (_) {}
          }
        }
      }
    } catch (e) { log(`  threw: ${e.message}`); }
    flushLog();
    log(`\n■ DONE`);
    flushLog();
  } catch (e) {
    log(`■ DONE (error): ${e.message}`); flushLog();
  }
});

// ─── 23. HIDDEN-API HUNT ───────────────────────────────────────────────────
// Walk uxp module deeply, probe for non-enumerable + Symbol-keyed props,
// try to require Adobe's first-party namespace names.
$("hidden-api-hunt")?.addEventListener("click", async () => {
  log("\n▶ START Hidden-API Hunt");
  flushLog();
  try {
    // --- 1. require("uxp") deep walk ---
    log("\n→ require(\"uxp\") deep walk:");
    const uxp = require("uxp");
    log(`  uxp own (enum): ${Object.keys(uxp).join(", ")}`);
    log(`  uxp ALL props (incl non-enum): ${Object.getOwnPropertyNames(uxp).sort().join(", ")}`);
    if (Object.getOwnPropertySymbols(uxp).length) {
      log(`  uxp Symbols: ${Object.getOwnPropertySymbols(uxp).map(String).join(", ")}`);
    }
    // recurse into namespaces
    for (const k of Object.getOwnPropertyNames(uxp).sort()) {
      try {
        const v = uxp[k];
        if (v && typeof v === "object") {
          const subKeys = Object.getOwnPropertyNames(v).filter(s => !["caller","arguments","length","name","prototype"].includes(s));
          log(`    uxp.${k}: ${typeof v} → keys: ${subKeys.slice(0, 30).join(", ")}${subKeys.length > 30 ? `... (+${subKeys.length-30})` : ''}`);
        } else if (typeof v === "function") {
          log(`    uxp.${k}: function`);
        }
      } catch (e) { log(`    uxp.${k}: throws ${e.message?.slice(0,40)}`); }
    }
    flushLog();

    // --- 2. premierepro non-enumerable + Symbol probe ---
    log("\n→ require(\"premierepro\") hidden-property hunt:");
    log(`  ALL props (incl non-enum): ${Object.getOwnPropertyNames(ppro).sort().join(", ")}`);
    const protoChain = [];
    let cur = ppro;
    while (cur) {
      const proto = Object.getPrototypeOf(cur);
      if (!proto || proto === Object.prototype) break;
      protoChain.push(Object.getOwnPropertyNames(proto));
      cur = proto;
    }
    log(`  prototype chain depth: ${protoChain.length}`);
    protoChain.forEach((p, i) => log(`    proto[${i}]: ${p.filter(x => !["constructor","__defineGetter__","__defineSetter__","__lookupGetter__","__lookupSetter__","__proto__","hasOwnProperty","isPrototypeOf","propertyIsEnumerable","toLocaleString","toString","valueOf"].includes(x)).join(", ")}`));
    flushLog();

    // Symbol-keyed props
    const symbols = Object.getOwnPropertySymbols(ppro);
    log(`  Symbols on ppro: ${symbols.length} ${symbols.map(s => s.toString()).join(", ")}`);

    // --- 3. Try require() of every Adobe-internal namespace name ---
    log("\n→ Trying require() of Adobe-internal namespace names:");
    const candidates = [
      "premierepro", "uxp",
      "dvatranscription", "sDMEvent", "mediaFoundation",
      "premierepro-internal", "ppro-internal",
      "dva", "dvacore", "dvaui",
      "graphics", "text", "transcription",
      "premierepro-private", "premierepro-experimental",
      "host", "premiere-host",
    ];
    for (const name of candidates) {
      try {
        const m = require(name);
        log(`  ✓ require("${name}") → ${typeof m}  keys: ${Object.keys(m || {}).slice(0, 20).join(", ")}`);
      } catch (e) {
        log(`  ✗ require("${name}") → ${e.message?.slice(0, 60)}`);
      }
    }
    flushLog();

    // --- 4. Look for any text-related symbols on ppro classes we know ---
    log("\n→ Re-walk ppro classes for non-enum props matching /text|graphic|source|setValue/i:");
    for (const cls of ["Sequence", "VideoClipTrackItem", "SequenceEditor", "Transcript", "TextSegments", "CaptionTrack", "Project"]) {
      if (!ppro[cls]) continue;
      const target = ppro[cls];
      const allProps = [
        ...Object.getOwnPropertyNames(target),
        ...(target.prototype ? Object.getOwnPropertyNames(target.prototype) : []),
      ];
      const hits = allProps.filter(k => /text|graphic|source|setvalue/i.test(k));
      if (hits.length) log(`  ppro.${cls}: ${hits.join(", ")}`);
    }

    log("\n■ DONE");
    flushLog();
  } catch (e) {
    log(`■ DONE (error): ${e.message}\n${e.stack || ''}`); flushLog();
  }
});

// ─── 24. Deep probe of uxp.host / hostPluginMessaging / pluginLoader ───────
$("hostmsg-hunt")?.addEventListener("click", async () => {
  log("\n▶ START Deep probe of uxp.host & messaging");
  flushLog();
  try {
    const uxp = require("uxp");

    function dumpDeep(obj, name, depth = 0, maxDepth = 3) {
      if (depth >= maxDepth || obj === null || obj === undefined) return;
      const allProps = [
        ...Object.getOwnPropertyNames(obj),
        ...Object.getOwnPropertySymbols(obj).map(s => s.toString()),
      ];
      const filtered = allProps.filter(p => !["caller","arguments","length","name","prototype","__proto__","constructor","__defineGetter__","__defineSetter__","__lookupGetter__","__lookupSetter__","hasOwnProperty","isPrototypeOf","propertyIsEnumerable","toLocaleString","toString","valueOf"].includes(p));
      log(`${"  ".repeat(depth)}${name} (${typeof obj}): ${filtered.length} props`);
      for (const k of filtered) {
        try {
          const v = obj[k];
          const t = typeof v;
          if (t === "function") {
            log(`${"  ".repeat(depth+1)}.${k}: function(${v.length} args)`);
          } else if (t === "object" && v !== null) {
            const subProps = [...Object.getOwnPropertyNames(v), ...Object.getOwnPropertySymbols(v).map(s => s.toString())].filter(p => !["caller","arguments","length","name","prototype","__proto__","constructor","__defineGetter__","__defineSetter__","__lookupGetter__","__lookupSetter__","hasOwnProperty","isPrototypeOf","propertyIsEnumerable","toLocaleString","toString","valueOf"].includes(p));
            log(`${"  ".repeat(depth+1)}.${k}: object (${subProps.length} props)`);
            if (depth < maxDepth - 1) {
              dumpDeep(v, `${name}.${k}`, depth + 2, maxDepth);
            }
          } else {
            log(`${"  ".repeat(depth+1)}.${k}: ${t} = ${String(v).slice(0, 80)}`);
          }
        } catch (e) {
          log(`${"  ".repeat(depth+1)}.${k}: <getter threw: ${e.message?.slice(0,40)}>`);
        }
      }
    }

    log("\n→ uxp.host:");
    dumpDeep(uxp.host, "uxp.host", 0, 3);
    flushLog();

    log("\n→ uxp.hostPluginMessaging:");
    dumpDeep(uxp.hostPluginMessaging, "uxp.hostPluginMessaging", 0, 3);
    flushLog();

    log("\n→ uxp.pluginLoader:");
    dumpDeep(uxp.pluginLoader, "uxp.pluginLoader", 0, 3);
    flushLog();

    log("\n→ uxp.pluginManager:");
    dumpDeep(uxp.pluginManager, "uxp.pluginManager", 0, 3);
    flushLog();

    log("\n→ uxp.versions:");
    dumpDeep(uxp.versions, "uxp.versions", 0, 2);
    flushLog();

    // Also peek at globalThis for top-level surprises
    log("\n→ globalThis own props (first 40 non-standard):");
    const standard = new Set(["globalThis","Infinity","NaN","undefined","Object","Function","Array","String","Boolean","Number","Symbol","Math","JSON","Date","RegExp","Error","Promise","Map","Set","WeakMap","WeakSet","Reflect","Proxy","ArrayBuffer","Uint8Array","Int8Array","Uint16Array","Int16Array","Uint32Array","Int32Array","Float32Array","Float64Array","DataView","Atomics","BigInt","SharedArrayBuffer","Console","console","window","document","setTimeout","clearTimeout","setInterval","clearInterval","require","module","exports","__filename","__dirname","TextEncoder","TextDecoder","URL","URLSearchParams","FormData","Blob","File","FileReader","Headers","Request","Response","fetch","performance","navigator","location","history","localStorage","sessionStorage","crypto","XMLHttpRequest","WebSocket","HTMLElement","Element","Node","Document","Window","Event","EventTarget","CustomEvent","queueMicrotask","structuredClone","atob","btoa","encodeURIComponent","decodeURIComponent","encodeURI","decodeURI","parseInt","parseFloat","isNaN","isFinite","escape","unescape","eval","RangeError","TypeError","SyntaxError","ReferenceError","URIError","EvalError","Intl","BigInt64Array","BigUint64Array","Uint8ClampedArray","FinalizationRegistry","WeakRef","AggregateError","globalThis"]);
    const interesting = Object.getOwnPropertyNames(globalThis).filter(n => !standard.has(n)).slice(0, 60);
    log(`  ${interesting.join(", ")}`);

    log("\n■ DONE");
    flushLog();
  } catch (e) {
    log(`■ DONE (error): ${e.message}\n${e.stack || ''}`); flushLog();
  }
});

// ─── 25. ★★ THE TEST: write Source Text via the documented Keyframe pattern ─
$("write-source-text-properly")?.addEventListener("click", async () => {
  log("\n▶ START Source Text write — DOCUMENTED PATTERN");
  log("(createKeyframe('HELLO FROM UXP') → createSetValueAction(kf) → executeTransaction)");
  log("(SAVE YOUR PRPROJ FIRST. If it crashes, this exact step is the culprit.)");
  flushLog();
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();
    const track = await _sequence.getVideoTrack(0);
    const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
    if (!items?.length) { log("✗ No V1 clips. Add a text graphic first."); flushLog(); return; }
    const clip = items[0];
    log(`✓ clip: "${await clip.getName()}"`); flushLog();

    const chain = await clip.getComponentChain();
    let textComp = null;
    for (let i = 0; i < await chain.getComponentCount(); i++) {
      const c = await chain.getComponentAtIndex(i);
      if (await c.getDisplayName() === "Text") { textComp = c; break; }
    }
    if (!textComp) { log("✗ No Text component"); flushLog(); return; }
    const sourceText = await textComp.getParam(0);
    log(`✓ Source Text param obtained (display="${sourceText.displayName}")`); flushLog();

    const TEST_STRING = "HELLO FROM UXP";
    log(`\n→ STEP 1: createKeyframe(${JSON.stringify(TEST_STRING)})`);
    flushLog();

    let kf;
    try {
      kf = sourceText.createKeyframe(TEST_STRING);
      log(`  ✓ createKeyframe returned: ${Object.prototype.toString.call(kf)}`);
      if (kf) {
        try { log(`  kf.value: ${Object.prototype.toString.call(kf.value)} = ${JSON.stringify(kf.value).slice(0, 200)}`); } catch (_) { log(`  kf.value: <getter threw>`); }
        try { log(`  kf.position: ${Object.prototype.toString.call(kf.position)}`); } catch (_) {}
      }
    } catch (e) {
      log(`  ✗ createKeyframe threw: ${e.message}`);
      log(`  → Source Text rejects strings via createKeyframe. Stopping.`);
      log(`■ DONE`); flushLog(); return;
    }
    flushLog();

    if (!kf) { log("  ✗ createKeyframe returned falsy"); log(`■ DONE`); flushLog(); return; }

    log(`\n→ STEP 2: createSetValueAction(kf)`); flushLog();
    let action;
    try {
      action = sourceText.createSetValueAction(kf);
      log(`  ✓ createSetValueAction returned: ${Object.prototype.toString.call(action)}`);
    } catch (e) {
      log(`  ✗ createSetValueAction threw: ${e.message}`);
      log(`■ DONE (action build failed)`); flushLog(); return;
    }
    flushLog();

    if (!action) { log("  ✗ no action"); log(`■ DONE`); flushLog(); return; }

    log(`\n→ STEP 3: executeTransaction (this is where prior fuzzing crashed Premiere)`); flushLog();
    try {
      const ok = await _project.executeTransaction((compoundAction) => {
        compoundAction.addAction(action);
      }, "Write Source Text via UXP");
      log(`  executeTransaction → ${ok}`);
      log(`  ★★ LOOK at the V1 graphic in the Program monitor.`);
      log(`  If text changed to "${TEST_STRING}" → THE WALL IS BROKEN.`);
      log(`  If unchanged but no crash → write was silent / didn't take.`);
      log(`  If Premiere is still here at all, that's a win vs. last time.`);
    } catch (e) {
      log(`  ✗ executeTransaction threw: ${e.message}`);
    }
    flushLog();

    log(`\n■ DONE`);
    flushLog();
  } catch (e) {
    log(`■ DONE (uncaught): ${e.message}`); flushLog();
  }
});

// ─── 26. ★★★ Probe torq-native, registerCoreModule, getApplicationModule ──
$("torq-hunt")?.addEventListener("click", async () => {
  log("\n▶ START torq-native + privileged probe");
  flushLog();

  log("\n→ require(\"torq-native\"):");
  let torq = null;
  try {
    torq = require("torq-native");
    log(`  ✓ require("torq-native") → ${typeof torq}`);
    log(`  keys (own): ${Object.keys(torq).join(", ")}`);
    log(`  keys (all): ${Object.getOwnPropertyNames(torq).join(", ")}`);
    log(`  symbols: ${Object.getOwnPropertySymbols(torq).map(String).join(", ")}`);
    if (torq && typeof torq === "object") {
      const proto = Object.getPrototypeOf(torq);
      if (proto) {
        const protoKeys = Object.getOwnPropertyNames(proto).filter(k => k !== "constructor");
        log(`  prototype keys: ${protoKeys.join(", ")}`);
      }
      if (typeof torq.native === "function") {
        log(`  torq.native is a function — calling torq.native("torq-native/plugin")`);
        try {
          const native = torq.native("torq-native/plugin");
          log(`    ✓ → ${typeof native}`);
          log(`    keys: ${Object.getOwnPropertyNames(native || {}).join(", ")}`);
          if (native?.registerCoreModule) {
            log(`    🎯 native.registerCoreModule EXISTS as ${typeof native.registerCoreModule}`);
          }
        } catch (e) { log(`    ✗ torq.native(...) threw: ${e.message}`); }
      }
    }
  } catch (e) {
    log(`  ✗ require("torq-native") threw: ${e.message}`);
  }
  flushLog();

  log("\n→ require(\"torq-native/plugin\"):");
  try {
    const tp = require("torq-native/plugin");
    log(`  ✓ → ${typeof tp}, keys: ${Object.getOwnPropertyNames(tp).join(", ")}`);
  } catch (e) {
    log(`  ✗ threw: ${e.message}`);
  }
  flushLog();

  log("\n→ ppro.getApplicationModule (possibly hidden):");
  try {
    if (typeof ppro.getApplicationModule === "function") {
      log(`  ✓ exists as function`);
      const am = ppro.getApplicationModule();
      log(`    returns: ${typeof am}`);
      if (am) log(`    keys: ${Object.getOwnPropertyNames(am).join(", ")}`);
    } else {
      log(`  ✗ not on ppro top-level`);
    }
  } catch (e) { log(`  threw: ${e.message}`); }
  flushLog();

  log("\n→ More require() candidates:");
  const more = [
    "torq-native/plugin", "torq",
    "premierepro/internal", "premierepro/private",
    "uxp/host", "uxp/plugin", "process", "node:process",
  ];
  for (const m of more) {
    try {
      const r = require(m);
      log(`  ✓ require("${m}") → ${typeof r}`);
      if (r && typeof r === "object") log(`    keys: ${Object.getOwnPropertyNames(r).slice(0, 15).join(", ")}`);
    } catch (e) {
      log(`  ✗ require("${m}") → ${(e.message || "").slice(0, 50)}`);
    }
  }
  flushLog();

  log("\n→ Reflect.ownKeys on uxp namespaces (catches Symbols + non-enum):");
  const uxp = require("uxp");
  for (const k of ["host", "hostPluginMessaging", "pluginManager", "pluginLoader", "versions"]) {
    if (!uxp[k]) { log(`  uxp.${k}: undefined`); continue; }
    const ownKeys = Reflect.ownKeys(uxp[k]);
    log(`  uxp.${k}: Reflect.ownKeys → ${ownKeys.length}: ${ownKeys.map(String).join(", ")}`);
    let cur = uxp[k];
    let depth = 0;
    while (cur && depth < 5) {
      const proto = Object.getPrototypeOf(cur);
      if (!proto || proto === Object.prototype) break;
      const protoKeys = Reflect.ownKeys(proto).filter(p => p !== "constructor");
      if (protoKeys.length) log(`    proto[${depth}]: ${protoKeys.map(String).join(", ")}`);
      cur = proto;
      depth++;
    }
  }
  flushLog();

  log("\n→ process info:");
  try {
    if (typeof process !== "undefined") {
      log(`  process.argv: ${JSON.stringify(process.argv || []).slice(0, 200)}`);
      log(`  process.platform: ${process.platform}`);
      log(`  process.versions keys: ${Object.keys(process.versions || {}).join(", ")}`);
    } else {
      log(`  process undefined`);
    }
  } catch (e) { log(`  process access threw: ${e.message}`); }

  log(`\n■ DONE`);
  flushLog();
});

// ─── 18. READ + WRITE Source Text on the V1 graphic clip ───────────────────
$("write-text-test")?.addEventListener("click", async () => {
  log("\n▶ START Source Text READ+WRITE test");
  log("(Needs a text graphic clip on V1 — same one you used for Button 17)");
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();

    const track = await _sequence.getVideoTrack(0);
    const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
    if (!items?.length) {
      log("✗ No clips on V1. Add a text graphic and re-run.");
      log("■ DONE"); return;
    }
    const clip = items[0];
    log(`✓ clip: "${await clip.getName()}"`);

    // Walk to the Text component
    const chain = await clip.getComponentChain();
    const compCount = await chain.getComponentCount();
    let textComp = null;
    for (let i = 0; i < compCount; i++) {
      const c = await chain.getComponentAtIndex(i);
      const dn = await c.getDisplayName();
      if (dn === "Text") { textComp = c; break; }
    }
    if (!textComp) { log("✗ no Text component"); log("■ DONE"); return; }
    log("✓ found Text component");

    const sourceTextParam = await textComp.getParam(0);
    log(`✓ param[0]: displayName="${sourceTextParam.displayName}"`);

    // STEP 1 — READ current value
    log("\n→ STEP 1 — READ current Source Text value:");
    let currentValue = null;
    if (typeof sourceTextParam.getStartValue === 'function') {
      try {
        currentValue = await sourceTextParam.getStartValue();
        log(`  getStartValue() → ${Object.prototype.toString.call(currentValue)}`);
        if (currentValue) {
          const proto = Object.getPrototypeOf(currentValue);
          const valMethods = Object.getOwnPropertyNames(proto).filter(k => k !== "constructor");
          log(`  value methods: ${valMethods.join(", ")}`);
          // Try every plausible accessor for the actual text
          for (const acc of ["text", "getText", "value", "getValue", "data", "getData", "stringValue", "asString", "toString"]) {
            try {
              if (typeof currentValue[acc] === 'function') {
                const r = await currentValue[acc]();
                log(`    .${acc}() → ${typeof r} ${typeof r === 'string' ? JSON.stringify(r).slice(0, 120) : ''}`);
              } else if (acc in currentValue) {
                log(`    .${acc} = ${typeof currentValue[acc]} ${typeof currentValue[acc] === 'string' ? JSON.stringify(currentValue[acc]).slice(0, 120) : ''}`);
              }
            } catch (e) { /* skip */ }
          }
        }
      } catch (e) { log(`  getStartValue threw: ${e.message}`); }
    }

    // STEP 2 — WRITE: try several value shapes
    log("\n→ STEP 2 — WRITE: try createSetValueAction with various inputs");
    const NEW_TEXT = "HELLO FROM UXP";
    const tries = [
      ["plain string", NEW_TEXT],
      ["{text: ...}", { text: NEW_TEXT }],
      ["{value: ...}", { value: NEW_TEXT }],
      ["currentValue (mutated text prop)", currentValue && (() => {
        try { currentValue.text = NEW_TEXT; } catch (_) {}
        return currentValue;
      })()],
      ["currentValue as-is", currentValue],
    ];
    for (const [label, val] of tries) {
      if (val === undefined) continue;
      try {
        const action = sourceTextParam.createSetValueAction(val);
        log(`  ${label}: createSetValueAction(...) → ${Object.prototype.toString.call(action)}`);
        if (action) {
          const ok = await _project.executeTransaction((compoundAction) => {
            compoundAction.addAction(action);
          }, `Set Source Text → ${label}`);
          log(`    executeTransaction → ${ok}`);
          if (ok) log(`    ★ Look at the V1 clip in the Program monitor — did the text change to "${NEW_TEXT}"?`);
        }
      } catch (e) {
        log(`  ${label} → threw: ${e.message?.slice(0, 100)}`);
      }
    }

    log("\n■ DONE");
  } catch (e) {
    log(`■ DONE (with error): ${e.message}\n${e.stack || ''}`);
  }
});

// ─── 17. Probe video clip's component chain for the Source Text param ──────
$("probe-text-component")?.addEventListener("click", async () => {
  log("\n▶ START Source Text component probe");
  log("(Make sure you have a TEXT GRAPHIC CLIP on a video track first — Graphics > New Layer > Text)");
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();

    // Walk every video track, find any clip
    const vCount = await _sequence.getVideoTrackCount();
    log(`\nVideo tracks: ${vCount}`);
    let target = null;
    let targetTrack = null;
    let targetIdx = null;
    for (let i = 0; i < vCount; i++) {
      const track = await _sequence.getVideoTrack(i);
      const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
      log(`  V${i+1}: ${items?.length ?? 0} clips`);
      if (items?.length && !target) {
        target = items[0];
        targetTrack = i + 1;
        targetIdx = 0;
      }
    }
    if (!target) {
      log(`\n✗ No video clips found. Add a text graphic to V1 first, then re-run.`);
      log(`■ DONE`);
      return;
    }

    log(`\n→ Probing first clip on V${targetTrack}:`);
    log(`  type: ${Object.prototype.toString.call(target)}`);
    log(`  name: ${typeof target.getName === 'function' ? await target.getName() : target.name}`);
    const proto = Object.getPrototypeOf(target);
    log(`  methods: ${Object.getOwnPropertyNames(proto).filter(k => k !== 'constructor').join(', ')}`);

    // Get the component chain
    if (typeof target.getComponentChain !== 'function') {
      log(`\n✗ No getComponentChain method. Can't probe text component.`);
      log(`■ DONE`); return;
    }
    const chain = await target.getComponentChain();
    log(`\n→ Component chain: ${Object.prototype.toString.call(chain)}`);
    const cproto = Object.getPrototypeOf(chain);
    log(`  methods: ${Object.getOwnPropertyNames(cproto).filter(k => k !== 'constructor').join(', ')}`);

    // Enumerate components
    let count = 0;
    if (typeof chain.getComponentCount === 'function') {
      count = await chain.getComponentCount();
    } else if (typeof chain.length !== 'undefined') {
      count = chain.length;
    }
    log(`\n→ Components in chain: ${count}`);

    for (let i = 0; i < count; i++) {
      let comp = null;
      try {
        if (typeof chain.getComponentAtIndex === 'function') comp = await chain.getComponentAtIndex(i);
        else if (typeof chain.getComponent === 'function') comp = await chain.getComponent(i);
      } catch (e) { log(`  ✗ getComponent(${i}) threw: ${e.message}`); continue; }
      if (!comp) continue;

      const compName = (typeof comp.getDisplayName === 'function') ? await comp.getDisplayName()
                     : (typeof comp.name === 'function') ? await comp.name()
                     : comp.name || '?';
      const cprto = Object.getPrototypeOf(comp);
      const compMethods = Object.getOwnPropertyNames(cprto).filter(k => k !== 'constructor');
      log(`  [${i}] "${compName}"  methods: ${compMethods.slice(0, 8).join(', ')}${compMethods.length > 8 ? '...' : ''}`);

      // If this looks like the Text/Source Text component, probe its params deeper
      if (/text|source\s*text|graphics/i.test(String(compName))) {
        log(`      ✨ This component name matches text/graphics — probing params:`);
        let pcount = 0;
        if (typeof comp.getParamCount === 'function') pcount = await comp.getParamCount();
        log(`      param count: ${pcount}`);
        const allParamMethods = new Set();
        for (let p = 0; p < pcount; p++) {
          let param = null;
          try { param = await comp.getParam(p); } catch (e) { continue; }
          if (!param) continue;

          // displayName is a property/getter, not a function — try every common shape
          let pname = '?';
          try {
            if (typeof param.displayName === 'function') pname = await param.displayName();
            else if (typeof param.displayName === 'string') pname = param.displayName;
            else if (param.displayName) pname = String(param.displayName);
          } catch (_) {}
          // Also try matchName (Adobe internal name like "Source Text")
          let matchName = '?';
          try {
            if (typeof param.getMatchName === 'function') matchName = await param.getMatchName();
            else if (typeof param.matchName === 'function') matchName = await param.matchName();
            else if (param.matchName) matchName = String(param.matchName);
          } catch (_) {}

          const pproto = Object.getPrototypeOf(param);
          const pmethods = Object.getOwnPropertyNames(pproto).filter(k => k !== 'constructor');
          pmethods.forEach(m => allParamMethods.add(m));

          // Try to read the current value at time 0
          let valDesc = '';
          try {
            if (typeof param.getValueAtTime === 'function') {
              const v = await param.getValueAtTime(ppro.TickTime.TIME_ZERO);
              valDesc = `  value@0: ${typeof v}`;
              if (v) {
                const vproto = Object.getPrototypeOf(v);
                const vmethods = Object.getOwnPropertyNames(vproto).filter(k => k !== 'constructor');
                valDesc += ` [${vmethods.slice(0, 6).join(', ')}${vmethods.length > 6 ? '...' : ''}]`;
              }
            }
          } catch (e) { valDesc = `  value@0 threw: ${e.message?.slice(0, 60)}`; }

          log(`        param[${p}] display="${pname}" match="${matchName}"${valDesc}`);
        }
        log(`\n      → ALL methods seen on params (full list): ${Array.from(allParamMethods).sort().join(', ')}`);
      }
    }

    log(`\n■ DONE`);
  } catch (e) {
    log(`■ DONE (with error): ${e.message}\n${e.stack || ''}`);
  }
});

// ─── 16. Probe every plausible UXP path to put VISIBLE TEXT on the timeline ─
$("probe-text-writes")?.addEventListener("click", async () => {
  log("\n▶ START Probe text-write paths");
  try {
    if (!_project) _project = await ppro.Project.getActiveProject();
    if (!_sequence) _sequence = await _project.getActiveSequence();

    // STRATEGY 1: SequenceEditor methods
    log("\n→ Probing SequenceEditor:");
    let seqEditor = null;
    try {
      seqEditor = await ppro.SequenceEditor.getEditor(_sequence);
      log(`  SequenceEditor.getEditor(seq) → ${Object.prototype.toString.call(seqEditor)}`);
      if (seqEditor) {
        const proto = Object.getPrototypeOf(seqEditor);
        log(`  methods: ${Object.getOwnPropertyNames(proto).filter(k => k !== "constructor").join(", ")}`);
      }
    } catch (e) { log(`  ✗ getEditor threw: ${e.message}`); }

    // STRATEGY 2: SequenceEditor.insertMogrtFromPath signature probe
    log("\n→ insertMogrtFromPath: trying common signatures");
    if (seqEditor && typeof seqEditor.insertMogrtFromPath === "function") {
      log(`  insertMogrtFromPath is a function on the editor instance ✓`);
      log(`  Adobe's typical signature: insertMogrtFromPath(path: string, time: TickTime, vTrack: number, aTrack: number)`);
      log(`  We'd need a real .mogrt file on disk to test. Skipping actual call.`);
    } else {
      log(`  insertMogrtFromPath not callable on this editor`);
    }

    // STRATEGY 3: createInsertProjectItemAction — insert an EXISTING bin item at a time
    log("\n→ createInsertProjectItemAction: needs a project item to insert");
    if (seqEditor && typeof seqEditor.createInsertProjectItemAction === "function") {
      log(`  available ✓`);
      // Find a project item to use as a guinea pig — get the first audio clip's project item
      try {
        const track = await _sequence.getAudioTrack(0);
        const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
        if (items?.[0]) {
          const pi = await items[0].getProjectItem();
          log(`  test item from A1: ${Object.prototype.toString.call(pi)} name="${pi?.name?.() || pi?.name || '?'}"`);
        }
      } catch (e) { log(`  couldn't get test item: ${e.message}`); }
    }

    // STRATEGY 4: search for ANY caption-creation method in the runtime
    log("\n→ Search for caption-creation methods in ppro namespace:");
    function deepSearch(obj, prefix = "ppro", depth = 0) {
      if (depth > 2 || !obj || typeof obj !== "object") return;
      const keys = Object.getOwnPropertyNames(obj);
      for (const k of keys) {
        if (/createCaption|fromTranscript|fromSourceClip|fromTextSegment|determineCaption/i.test(k)) {
          let typeStr = "";
          try { typeStr = typeof obj[k]; } catch (_) {}
          log(`  ${prefix}.${k}  (${typeStr})`);
        }
        // Recurse into namespace-like classes
        if (depth < 2 && obj[k] && typeof obj[k] === "object" && !Array.isArray(obj[k])) {
          try { deepSearch(obj[k], `${prefix}.${k}`, depth + 1); } catch (_) {}
        }
      }
    }
    deepSearch(ppro);

    // Also probe if Transcript has create-caption methods
    log("\n→ Methods on ppro.Transcript that mention caption/segment:");
    for (const k of Object.getOwnPropertyNames(ppro.Transcript || {})) {
      if (/caption|segment|track/i.test(k)) {
        log(`  ppro.Transcript.${k}  (${typeof ppro.Transcript[k]})`);
      }
    }

    log(`\n■ DONE`);
  } catch (e) {
    log(`■ DONE (with error): ${e.message}\n${e.stack || ""}`);
  }
});

// ─── 15. Load real transcript from /tmp/karaoke_words.json ─────────────────
$("load-real-transcript")?.addEventListener("click", async () => {
  log("\n▶ Loading /tmp/karaoke_words.json ...");
  try {
    const words = readKaraokeJson();
    if (!words.length) throw new Error("no words in file");
    _activeWords = words;
    _autoReloadJson = true;  // every subsequent regen will re-read the file
    log(`✓ loaded ${words.length} words. Auto-reload ON — every DIRTY will re-read the JSON.`);
    log(`  first 5: ${words.slice(0, 5).map(w => `"${w.text}"@${w.t}s`).join(", ")}`);
    log(`  last 3:  ${words.slice(-3).map(w => `"${w.text}"@${w.t}s`).join(", ")}`);
    log("Now: leave karaoke_watcher.py running in a terminal. Edit transcript in Premiere, Cmd+S, watch the timeline markers refresh.");
    // Trigger an immediate render
    if (_loopHandler) {
      log("(Triggering an immediate regen since loop is running)");
      try { await regenerateKaraoke(_activeWords); }
      catch (e) { log(`  immediate regen failed: ${e.message}`); }
    }
  } catch (e) {
    log(`✗ failed: ${e.message}`);
  }
});

// ─── 14. Exhaustive probe of Transcript.exportToJSON ───────────────────────
$("probe-export-json")?.addEventListener("click", async () => {
  log("\n▶ START exhaustive Transcript.exportToJSON probe");
  try {
    const project = await ppro.Project.getActiveProject();
    const sequence = await project.getActiveSequence();

    // Get the first audio clip and its master clip
    const track = await sequence.getAudioTrack(0);
    const items = await track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false);
    const trackItem = items && items[0];
    const masterClip = trackItem ? await trackItem.getProjectItem() : null;
    const componentChain = trackItem && typeof trackItem.getComponentChain === "function"
      ? await trackItem.getComponentChain() : null;

    log(`  trackItem: ${trackItem ? "yes" : "no"}`);
    log(`  masterClip: ${masterClip ? "yes" : "no"}`);
    log(`  componentChain: ${componentChain ? "yes" : "no"}`);

    // Get all bin items too — maybe the master clip in the bin is "richer"
    const root = await project.getRootItem();
    const binItems = root && typeof root.getItems === "function" ? await root.getItems() : [];
    log(`  bin items count: ${binItems?.length ?? 0}`);

    // Try every plausible argument and signature
    const targets = [
      ["no-arg", undefined],
      ["sequence", sequence],
      ["project", project],
      ["trackItem", trackItem],
      ["masterClip (from trackItem)", masterClip],
      ["componentChain", componentChain],
      ["binItems[0]", binItems?.[0]],
      ["binItems[1]", binItems?.[1]],
      ["binItems[2]", binItems?.[2]],
    ];

    for (const [label, arg] of targets) {
      if (arg === undefined && label !== "no-arg") continue;
      // Try Transcript.exportToJSON
      try {
        const r = arg === undefined
          ? await ppro.Transcript.exportToJSON()
          : await ppro.Transcript.exportToJSON(arg);
        const t = typeof r;
        const len = (typeof r === "string") ? r.length : "n/a";
        log(`  ✓ Transcript.exportToJSON(${label}) → ${t} length=${len}`);
        if (typeof r === "string" && r.length > 10) {
          _lastTranscriptJSON = r;
          log(`    First 500 chars:\n${r.slice(0, 500)}`);
          log(`\n■ DONE  GOT TRANSCRIPT JSON via "${label}"`);
          return;
        }
      } catch (e) {
        log(`  ✗ Transcript.exportToJSON(${label}) threw: ${e.message}`);
      }
      // Same with TextSegments.exportToJSON
      try {
        const r = arg === undefined
          ? await ppro.TextSegments.exportToJSON()
          : await ppro.TextSegments.exportToJSON(arg);
        const t = typeof r;
        const len = (typeof r === "string") ? r.length : "n/a";
        log(`  ✓ TextSegments.exportToJSON(${label}) → ${t} length=${len}`);
        if (typeof r === "string" && r.length > 10) {
          _lastTranscriptJSON = r;
          log(`    First 500 chars:\n${r.slice(0, 500)}`);
          log(`\n■ DONE  GOT TRANSCRIPT JSON via TextSegments(${label})`);
          return;
        }
      } catch (e) {
        log(`  ✗ TextSegments.exportToJSON(${label}) threw: ${e.message}`);
      }
    }

    log(`\n■ DONE — no exportToJSON variant returned data. FlatBuffers crack is the next path.`);
  } catch (e) {
    log(`■ DONE (with error): ${e.message}\n${e.stack || ""}`);
  }
});

$("copy-log")?.addEventListener("click", async () => {
  try {
    const uxp = require("uxp");
    await uxp.clipboard.copyText($("log").textContent);
    log("(log copied via UXP clipboard)");
  } catch (e) {
    log("(UXP clipboard failed:", e.message, "— try Save to /tmp instead)");
  }
});

$("save-log")?.addEventListener("click", async () => {
  try {
    const fs = require("fs");
    fs.writeFileSync("/tmp/uxp_probe.log", $("log").textContent);
    log("(saved to /tmp/uxp_probe.log)");
  } catch (e) {
    log("(save failed:", e.message, ")");
  }
});

$("clear-log")?.addEventListener("click", () => {
  $("log").textContent = "";
});

log("Probe ready. Click buttons in order 1→6.");
log("Manifest API version: 6, target: Premiere Pro 25.6+");
