import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

// A lógica de CSV mora dentro do HTML (arquivo único, sem dependências); o teste a extrai e executa.
// Dentro da imagem de testes só existe a pasta app/: sem o HTML (fora do app), o teste não se aplica.
const caminho = resolve(__dirname, "../../scripts/rotulagem/rotular.html");
const existe = existsSync(caminho);
const html = existe ? readFileSync(caminho, "utf-8") : "<script id=\"logica\"></script>";
const trecho = /<script id="logica">([\s\S]*?)<\/script>/.exec(html)![1]!;
const lib = new Function(`${trecho}; return { parseCsv, gerarCsv, lerPlanilha, escreverPlanilha, chaveProgresso, TEMAS, COLUNAS };`)() as {
  parseCsv: (t: string) => string[][];
  gerarCsv: (l: string[][]) => string;
  lerPlanilha: (t: string) => Record<string, string>[];
  escreverPlanilha: (r: Record<string, string>[]) => string;
  chaveProgresso: (r: { id_amostra: string }[]) => string;
  TEMAS: string[][];
  COLUNAS: string[];
};

const registro = (id: string, pergunta: string, resposta: string) => ({ id_amostra: id, conversa_id: "9" + id, pergunta, resposta, tema_vinicius: "", recusa_vinicius: "" });

describe.skipIf(!existe)("CSV da rotulagem", () => {
  it("ida e volta com ';', aspas e quebras de linha dentro do texto", () => {
    const regs = [
      registro("1", 'Diga "olá"; depois\numa segunda linha\r\ne uma terceira', "Resposta; com ponto e vírgula e \"aspas\"\n\nlinha em branco"),
      registro("2", "simples", ""),
      registro("3", '"', ";;;"),
    ];
    const csv = lib.escreverPlanilha(regs);
    expect(csv.charCodeAt(0)).toBe(0xfeff);
    expect(lib.lerPlanilha(csv)).toEqual(regs);
  });

  it("lê entrada no formato do seed (BOM, todos os campos entre aspas, LF)", () => {
    const entrada = '﻿"id_amostra";"conversa_id";"pergunta";"resposta";"tema_vinicius";"recusa_vinicius"\n"1";"10";"a;b";"c\nd";"";""\n';
    expect(lib.lerPlanilha(entrada)).toEqual([{ id_amostra: "1", conversa_id: "10", pergunta: "a;b", resposta: "c\nd", tema_vinicius: "", recusa_vinicius: "" }]);
  });

  it("preserva as colunas e a ordem, e recusa cabeçalho errado", () => {
    expect(lib.parseCsv(lib.escreverPlanilha([registro("1", "p", "r")]))[0]).toEqual(lib.COLUNAS);
    expect(() => lib.lerPlanilha('"a";"b"\n"1";"2"\n')).toThrow(/Cabeçalho/);
  });

  it("os 8 temas são exatamente os da taxonomia", () => {
    expect(lib.TEMAS.map((t) => t[0])).toEqual([
      "estudo/dever de casa", "programação/TI", "escrita e tradução", "trabalho/negócios",
      "criação/ficção e roleplay", "informação geral/curiosidade", "conversa pessoal/conselho", "outros/indefinido",
    ]);
  });

  it("a chave do progresso depende só dos ids, não do texto", () => {
    const a = lib.chaveProgresso([registro("1", "x", "y"), registro("2", "z", "w")]);
    const b = lib.chaveProgresso([registro("1", "outro", "texto"), registro("2", "q", "r")]);
    expect(a).toBe(b);
  });
});
