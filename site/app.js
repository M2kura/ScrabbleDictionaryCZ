// UI for the dictionary API served by server/app.py.

const SOURCES = {
  M: "MorfFlex CZ",
  H: "Hunspell (LibreOffice)",
  C: "Wikislovník",
  E: "Anglický Wiktionary",
  D: "Wikidata",
};
const TIER = ["spisovné", "zastaralé nebo starší pravopis", "hovorové, nářeční nebo slangové"];
const POS = {
  N: "podstatné jméno", A: "přídavné jméno", P: "zájmeno", C: "číslovka", V: "sloveso",
  D: "příslovce", R: "předložka", J: "spojka", T: "částice", I: "citoslovce",
};
// Official Czech Scrabble tile values; q and w have no tile and need a blank.
const POINTS = {
  a: 1, e: 1, i: 1, n: 1, o: 1, s: 1, t: 1, v: 1, d: 1, k: 1, l: 1, p: 1, r: 1,
  c: 2, h: 2, í: 2, m: 2, u: 2, á: 2, j: 2, y: 2, z: 2,
  b: 3, é: 3, ě: 3,
  ř: 4, š: 4, ý: 4, č: 4, ů: 4, ž: 4,
  f: 5, g: 5, ú: 5,
  ň: 6, ó: 7, ť: 7, ď: 8, x: 10, q: 0, w: 0,
};

const $ = (id) => document.getElementById(id);
const input = $("q"), tilesEl = $("tiles"), resultEl = $("result");

// Relative URLs, so the app also works under a path prefix (/scrabble/).
async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function lookup(list) {
  const { results } = await api("api/lookup?q=" + encodeURIComponent(list.join(" ")));
  return results;
}

function score(word) {
  return [...word].reduce((s, ch) => s + (POINTS[ch] ?? 0), 0);
}

function normalise(s) {
  return s.normalize("NFC").toLocaleLowerCase("cs").trim();
}

function words(raw) {
  return normalise(raw).split(/[\s,;]+/).filter(Boolean);
}

function mode() {
  return +document.querySelector('input[name="mode"]:checked').value;
}

function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const c of children.flat(Infinity)) if (c != null) e.append(c);
  return e;
}

function renderTiles(list) {
  tilesEl.replaceChildren(
    ...list.slice(0, 6).map((w) =>
      el("span", { class: "word" },
        [...w].slice(0, 20).map((ch) =>
          el("span", { class: "tile" + (POINTS[ch] === 0 ? " blank" : "") },
            ch.toLocaleUpperCase("cs"),
            el("sub", {}, POINTS[ch] === undefined ? "" : String(POINTS[ch])))))));
}

function verdict(r, m) {
  if (!r.problem && r.found && r.tier <= m) return "valid";
  if (!r.problem && r.found) return "loose";
  return "invalid";
}

const VERDICT_TEXT = {
  valid: "Platné slovo",
  loose: ["", "Jen zastaralý tvar", "Jen hovorový tvar"],
  invalid: "Slovo nenalezeno",
};

function lemmaLine(r) {
  if (!r.lemmas.length) return null;
  const parts = r.lemmas.map(({ pos, lemma }, i) => {
    const desc = POS[pos];
    const self = lemma === r.word;
    return [
      i ? "; " : "",
      self ? (i ? "základní tvar" : "Základní tvar") : [i ? "tvar slova " : "Tvar slova ", wordLink(lemma)],
      desc ? ` (${desc})` : "",
    ];
  });
  return el("p", { class: "lemma" }, parts);
}

function wordLink(w) {
  return el("a", { href: "#" + encodeURIComponent(w), onclick: (e) => { e.preventDefault(); search(w); } }, w);
}

function renderDetail(r, m) {
  const v = verdict(r, m);
  const pts = score(r.word);
  const card = el("article", { class: "card " + v },
    el("p", { class: "verdict" }, v === "loose" ? VERDICT_TEXT.loose[r.tier] : VERDICT_TEXT[v]),
    el("p", { class: "meta" },
      el("strong", {}, r.word), ` za ${pts} ${pts === 1 ? "bod" : pts < 5 ? "body" : "bodů"} bez prémií`));

  if (r.problem) {
    card.append(el("p", {}, r.problem));
  } else if (r.found) {
    card.append(...[
      el("p", {}, v === "loose"
        ? `Slovo je ve slovnících jen jako ${TIER[r.tier]}. Platí v režimu „${r.tier === 1 ? "I zastaralé" : "I hovorové"}“.`
        : `Rejstřík: ${TIER[r.tier]}.`),
      lemmaLine(r),
      el("p", { class: "found-label" }, `Najdete ho v ${r.sources.length} z 5 slovníků:`),
      el("ul", { class: "found-in" },
        Object.entries(SOURCES).map(([k, name]) => {
          const has = r.sources.includes(k);
          return el("li", { class: has ? "yes" : "no" },
            el("span", { class: "visually-hidden" }, has ? "ano: " : "ne: "), name);
        })),
      r.sources.length === 1
        ? el("p", { class: "note" }, "Slovo zná jen jeden zdroj. Může jít o vzácný nebo automaticky odvozený tvar.")
        : null,
    ].filter(Boolean));
  } else {
    card.append(el("p", {}, "Žádný z pěti slovníků tento tvar nezná."));
    if (r.suggestions?.length) {
      card.append(el("p", { class: "suggest" }, "S jinou diakritikou platí: ",
        r.suggestions.map((s, i) => [i ? ", " : "", wordLink(s.word)])));
    } else {
      card.append(el("p", {}, "Zkontrolujte diakritiku a koncovku."));
    }
  }

  if (r.neighbours?.length) {
    card.append(el("nav", { class: "neighbours", "aria-label": "Abecedně sousední slova" },
      el("span", {}, "Abecedně vedle: "),
      r.neighbours.map((w, i) => [i ? ", " : "", wordLink(w)])));
  }
  return card;
}

function renderList(results, m) {
  const all = results.every((r) => verdict(r, m) === "valid");
  return el("article", { class: "card " + (all ? "valid" : "invalid") },
    el("p", { class: "verdict" }, all ? "Všechna slova platí" : "Některé slovo neplatí"),
    el("ul", { class: "list" },
      results.map((r) => {
        const v = verdict(r, m);
        const alt = r.suggestions?.[0];
        return el("li", { class: v },
          wordLink(r.word),
          el("span", {},
            v === "valid" ? `platí, ${score(r.word)} b.`
              : v === "loose" ? TIER[r.tier]
              : r.problem ? "nelze zahrát"
              : alt ? ["nenalezeno, platí ", wordLink(alt.word)]
              : "nenalezeno"));
      })));
}

let lastResults = null;
let seq = 0;

async function run() {
  const list = words(input.value);
  renderTiles(list);
  const my = ++seq;
  if (!list.length) {
    lastResults = null;
    resultEl.replaceChildren();
    return;
  }
  try {
    const results = await lookup(list.slice(0, 12));
    if (my !== seq) return;
    lastResults = results;
    render();
    history.replaceState(null, "", "#" + encodeURIComponent(list.join(" ")));
  } catch (err) {
    if (my !== seq) return;
    resultEl.replaceChildren(el("article", { class: "card invalid" },
      el("p", { class: "verdict" }, "Slovník se nenačetl"),
      el("p", {}, `Zkontrolujte připojení a zkuste to znovu. (${err.message})`)));
  }
}

function render() {
  if (!lastResults) return;
  const m = mode();
  resultEl.replaceChildren(lastResults.length === 1 ? renderDetail(lastResults[0], m) : renderList(lastResults, m));
}

function search(w) {
  input.value = w;
  run();
  input.focus();
}

let timer;
input.addEventListener("input", () => {
  renderTiles(words(input.value));
  clearTimeout(timer);
  timer = setTimeout(run, 180);
});
$("search").addEventListener("submit", (e) => { e.preventDefault(); clearTimeout(timer); run(); });

for (const r of document.querySelectorAll('input[name="mode"]')) {
  r.addEventListener("change", () => {
    try { localStorage.setItem("mode", r.value); } catch {}
    render();
  });
}
try {
  const saved = localStorage.getItem("mode");
  if (saved) document.querySelector(`input[name="mode"][value="${saved}"]`).checked = true;
} catch {}

api("api/stats").then((st) => {
  const n = st.words.toLocaleString("cs");
  $("stats").textContent = `Celkem ${n} tvarů slov, sestaveno ${new Date(st.version).toLocaleDateString("cs")}.`;
}).catch(() => {});

if (location.hash.length > 1) {
  input.value = decodeURIComponent(location.hash.slice(1));
  run();
}
