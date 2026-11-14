// Varredura do painel: clica em tudo que é clicável (2 níveis) e guarda o texto e a captura de cada estado.
// Uso: node varredura.mjs <pasta_saida> [rotas separadas por vírgula] [base]
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const saida = process.argv[2];
const rotas = (process.argv[3] ?? ",fatores,dados").split(",");
const base = process.argv[4] ?? "http://localhost:3000";
mkdirSync(saida, { recursive: true });
const chrome = process.env.CHROME ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const porta = 9377;
const proc = spawn(chrome, ["--headless=new", "--disable-gpu", "--force-prefers-reduced-motion", `--remote-debugging-port=${porta}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "varre-"))}`, "about:blank"], { stdio: "ignore" });
const dorme = (ms) => new Promise((r) => setTimeout(r, ms));
await dorme(3000);
const alvos = await (await fetch(`http://127.0.0.1:${porta}/json`)).json();
const ws = new WebSocket(alvos.find((a) => a.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pend = {};
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) pend[m.id](m.result); };
const cmd = (method, params = {}) => new Promise((r) => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
const js = async (expr) => { const r = await cmd("Runtime.evaluate", { returnByValue: true, awaitPromise: true, expression: expr }); return r?.result?.value; };

// Funções que rodam na página
const NA_PAGINA = `
window.__clicaveis = () => {
  const sel = "button, [role=button], [role=tab], summary, [tabindex='0'], a[href^='#']";
  const vistos = [];
  for (const el of document.querySelectorAll(sel)) {
    if (el.closest("header nav") || el.closest("nav[aria-label]") && el.tagName === "A") continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const st = getComputedStyle(el);
    if (st.visibility === "hidden" || st.display === "none" || el.disabled) continue;
    if (vistos.some((v) => v.contains(el) && v !== el && v.tagName !== "DIV" )) continue;
    vistos.push(el);
  }
  window.__lista = vistos;
  return vistos.map((el) => ((el.getAttribute("aria-label") || el.innerText || el.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 70)) + (el.closest("[role=dialog], aside, dialog") ? " [no painel]" : ""));
};
window.__painel = () => document.querySelector("[role=dialog], dialog[open], aside[data-aberto], aside");
window.__estado = () => {
  const p = window.__painel();
  const alvo = p || document.querySelector("main") || document.body;
  return JSON.stringify({ temPainel: !!p, texto: alvo.innerText, altura: alvo.scrollHeight, visivel: alvo.clientHeight, corpo: document.body.innerText.length });
};
window.__abreTudo = () => { const p = window.__painel() || document; let n = 0; for (const d of p.querySelectorAll("details:not([open])")) { d.open = true; n++; } return n; };
`;

const resultados = [];
let n = 0;
async function abre(rota) {
  await cmd("Page.navigate", { url: `${base}/${rota}` });
  await dorme(6500);
  await js(NA_PAGINA);
}
async function captura(nome) {
  const r = await cmd("Page.captureScreenshot", { format: "jpeg", quality: 60 });
  if (r?.data) writeFileSync(join(saida, nome + ".jpg"), Buffer.from(r.data, "base64"));
}
async function registra(rota, caminho, extra = {}) {
  const e = JSON.parse(await js("window.__estado()"));
  const nome = `${String(++n).padStart(3, "0")}`;
  await captura(nome);
  const abertos = await js("window.__abreTudo()");
  let textoTudo = null, alturaTudo = null;
  if (abertos > 0) {
    await dorme(300);
    const e2 = JSON.parse(await js("window.__estado()"));
    textoTudo = e2.texto; alturaTudo = e2.altura;
    await captura(nome + "b");
  }
  resultados.push({ nome, rota: "/" + rota, caminho, ...extra, temPainel: e.temPainel, palavras: e.texto.trim().split(/\s+/).length, altura: e.altura, visivel: e.visivel, texto: e.texto, recolhidos: abertos, palavrasComRecolhidos: textoTudo ? textoTudo.trim().split(/\s+/).length : null, alturaComRecolhidos: alturaTudo, textoComRecolhidos: textoTudo });
  console.log(nome, "/" + rota, caminho.join(" > "), e.temPainel ? "[painel]" : "", e.texto.trim().split(/\s+/).length, "palavras");
}

await cmd("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
for (const rota of rotas) {
  await abre(rota);
  const nivel1 = await js("window.__clicaveis()");
  const textoBase = JSON.parse(await js("window.__estado()")).texto;
  await registra(rota, ["(estado inicial)"]);
  for (let i = 0; i < nivel1.length; i++) {
    await abre(rota);
    const l1 = await js("window.__clicaveis()");
    if (l1[i] !== nivel1[i]) { console.log("  rótulo mudou, pulo:", nivel1[i]); continue; }
    await js(`window.__lista[${i}].click()`);
    await dorme(900);
    const depois = JSON.parse(await js("window.__estado()"));
    if (!depois.temPainel && depois.texto === textoBase) { resultados.push({ rota: "/" + rota, caminho: [nivel1[i]], semEfeito: true }); continue; }
    await registra(rota, [nivel1[i]]);
    // nível 2: o que apareceu de novo para clicar
    await abre(rota);
    await js("window.__clicaveis()");
    await js(`window.__lista[${i}].click()`);
    await dorme(900);
    const nivel2 = await js("window.__clicaveis()");
    const novos = nivel2.map((r, j) => [r, j]).filter(([r]) => !nivel1.includes(r) && !/^(fechar|×|x)$/i.test(r.replace(" [no painel]", "")));
    for (const [rot, j] of novos) {
      await abre(rota);
      await js("window.__clicaveis()");
      await js(`window.__lista[${i}].click()`);
      await dorme(900);
      const l2 = await js("window.__clicaveis()");
      if (l2[j] !== rot) continue;
      const antes = JSON.parse(await js("window.__estado()")).texto;
      await js(`window.__lista[${j}].click()`);
      await dorme(900);
      const e = JSON.parse(await js("window.__estado()"));
      if (e.texto === antes) continue;
      await registra(rota, [nivel1[i], rot]);
    }
  }
}
writeFileSync(join(saida, "varredura.json"), JSON.stringify(resultados, null, 1));
console.log("estados:", resultados.filter((r) => !r.semEfeito).length, "sem efeito:", resultados.filter((r) => r.semEfeito).length);
ws.close();
proc.kill();
process.exit(0);
