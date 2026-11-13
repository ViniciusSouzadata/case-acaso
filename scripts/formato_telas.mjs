// Formato "painel": a 1280×720 as 3 telas não rolam na vertical no estado inicial; a 390 e a 1280 não rolam na horizontal.
// Uso (app no ar): node scripts/formato_telas.mjs [http://localhost:3000]. Precisa do Chrome (CHROME=caminho); sai com 1 se falhar.
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const base = process.argv[2] ?? "http://localhost:3000";
const chrome = process.env.CHROME ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const porta = 9341;
const proc = spawn(chrome, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${porta}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "formato-"))}`, "about:blank"], { stdio: "ignore" });
await new Promise((r) => setTimeout(r, 3000));
const alvos = await (await fetch(`http://127.0.0.1:${porta}/json`)).json();
const ws = new WebSocket(alvos.find((a) => a.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pend = {};
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) pend[m.id](m.result); };
const cmd = (method, params = {}) => new Promise((r) => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
const medida = () => JSON.stringify({ h: document.documentElement.scrollHeight, sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, carregou: document.querySelectorAll("[data-testid='frase-resposta'],[data-testid='frase-confianca'],h1").length > 0 });

let falhas = 0;
for (const [w, h] of [[1280, 720], [390, 844]]) for (const rota of ["", "fatores", "dados"]) {
  await cmd("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
  await cmd("Page.navigate", { url: `${base}/${rota}` });
  await new Promise((r) => setTimeout(r, 5000));
  const m = JSON.parse((await cmd("Runtime.evaluate", { returnByValue: true, expression: `(${medida})()` })).result.value);
  const semRolagemH = m.sw <= m.cw;
  const semRolagemV = w !== 1280 || m.h <= h;
  const ok = m.carregou && semRolagemH && semRolagemV;
  if (!ok) falhas++;
  console.log(`${ok ? "OK   " : "FALHA"} ${w}x${h} /${rota}  altura=${m.h}  largura=${m.sw}/${m.cw}`);
}
ws.close();
proc.kill();
process.exit(falhas ? 1 : 0);
