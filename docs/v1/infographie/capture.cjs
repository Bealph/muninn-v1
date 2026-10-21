// Rendus d'une infographie : PDF et PNG de la page entière, une image PNG par section.
// Usage : node capture.cjs <fichier.html> <dossier de sortie> <nom>
// Puppeteer est pris dans le dossier Node désigné par OUTILS_NODE (par défaut, la boîte à outils
// du poste), avec sa configuration de navigateur `puppeteer-edge.json` si elle existe.
// Largeur 1 200 px à l'échelle 2 : les rendus versionnés font 2 400 px de large.
const { createRequire } = require("module");
const path = require("path");
const fs = require("fs");
const outils = process.env.OUTILS_NODE || "C:/Users/adiallo/dev/ai-toolbox/ts";
const puppeteer = createRequire(path.join(outils, "package.json"))("puppeteer");
const fichierConfig = path.join(outils, "puppeteer-edge.json");
const config = fs.existsSync(fichierConfig) ? require(fichierConfig) : {};
(async () => {
  const [html, sortie, nom] = process.argv.slice(2);
  fs.mkdirSync(path.join(sortie, "sections"), { recursive: true });
  const nav = await puppeteer.launch(config);
  const page = await nav.newPage();
  await page.setViewport({ width: 1200, height: 900, deviceScaleFactor: 2 });
  await page.goto(require("url").pathToFileURL(path.resolve(html)).href, { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(sortie, nom + ".png"), fullPage: true });
  const hauteur = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.pdf({ path: path.join(sortie, nom + ".pdf"), width: "1200px", height: hauteur + 1 + "px", printBackground: true, pageRanges: "1" });
  const ids = await page.$$eval("section[id]", (s) => s.map((e) => e.id));
  for (const [i, id] of ids.entries()) {
    const el = await page.$("#" + id);
    const fichier = String(i + 1).padStart(2, "0") + "-" + id.replace(/^s-/, "") + ".png";
    await el.screenshot({ path: path.join(sortie, "sections", fichier) });
    console.log(fichier);
  }
  await nav.close();
})().catch((e) => { console.error(e); process.exit(1); });
