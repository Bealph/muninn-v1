// Fonctions communes des vitrines de Muninn, insérées dans l'IIFE de chaque page. Attend
// `PREFIXE` (clé de mémoire locale propre à la page) et les éléments `#bascule-theme`.
const $ = (id) => document.getElementById(id);

// Construction sûre : le texte venu des flux n'est jamais interprété comme du HTML.
function el(tag, attrs, ...enfants) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const e of enfants.flat()) if (e !== null && e !== undefined && e !== false) n.append(e);
  return n;
}
const sur = (href) => typeof href === "string" && href.startsWith("https://");
function lien(texte, href) {
  return sur(href) ? el("a", { href, target: "_blank", rel: "noopener noreferrer" }, texte, el("span", { class: "evitement", text: " (nouvel onglet)" })) : document.createTextNode(texte);
}
function segs(liste) {
  const f = document.createDocumentFragment();
  for (const s of liste || []) {
    if ("code" in s) f.append(el("code", { text: s.code }));
    else if ("a" in s) f.append(lien(s.a, s.href));
    else if ("b" in s) f.append(el("strong", {}, segs(s.b)));
    else f.append(document.createTextNode(s.t));
  }
  return f;
}
const texteDe = (liste) => (liste || []).map((s) => s.t ?? s.code ?? s.a ?? (s.b ? texteDe(s.b) : "")).join("");

// Mémoire propre à ce navigateur : préférences et entrées vues, jamais indispensable.
const memoire = {
  lire(cle, defaut) { try { const v = localStorage.getItem(PREFIXE + cle); return v === null ? defaut : JSON.parse(v); } catch { return defaut; } },
  ecrire(cle, v) { try { localStorage.setItem(PREFIXE + cle, JSON.stringify(v)); } catch { /* sans mémoire */ } },
};

// Thème : celui du système par défaut ; un choix manuel est mémorisé dans ce navigateur.
const racineDoc = document.documentElement;
const themeChoisi = memoire.lire("theme", "");
if (themeChoisi === "dark" || themeChoisi === "light") racineDoc.setAttribute("data-theme", themeChoisi);
const systemeSombre = () => typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches;
const estSombre = () => (racineDoc.getAttribute("data-theme") || (systemeSombre() ? "dark" : "light")) === "dark";
const boutonTheme = $("bascule-theme");
const majTheme = () => boutonTheme.setAttribute("aria-pressed", estSombre() ? "true" : "false");
boutonTheme.addEventListener("click", () => {
  const theme = estSombre() ? "light" : "dark";
  racineDoc.setAttribute("data-theme", theme);
  memoire.ecrire("theme", theme);
  majTheme();
});
majTheme();

const mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
const jours = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
function dateLongue(iso, avecJour) {
  const [a, m, j] = iso.split("-").map(Number);
  const d = new Date(Date.UTC(a, m - 1, j));
  return (avecJour ? jours[d.getUTCDay()] + " " : "") + j + (j === 1 ? "er" : "") + " " + mois[m - 1] + " " + a;
}
