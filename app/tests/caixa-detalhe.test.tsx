// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { act } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CaixaDetalhe } from "@/components/CaixaDetalhe";
import { DetalheFator } from "@/components/DetalheFator";
import { prepararFloresta, type EfeitoApi } from "@/lib/floresta";

afterEach(cleanup);

function Exemplo({ largo = false }: { largo?: boolean }) {
  const [aberto, setAberto] = useState(false);
  return (
    <div>
      <button type="button" onClick={() => setAberto(true)}>Abrir detalhe</button>
      {aberto ? (
        <CaixaDetalhe titulo="Título do detalhe" largo={largo} onFechar={() => setAberto(false)}>
          <p>Conteúdo</p>
          <button type="button">Outro botão</button>
        </CaixaDetalhe>
      ) : null}
    </div>
  );
}

describe("CaixaDetalhe — caixa central que abre ao clicar", () => {
  it("abre ao clicar, com role=dialog, aria-modal e título ligado por aria-labelledby", () => {
    render(<Exemplo />);
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
    const d = screen.getByRole("dialog", { name: "Título do detalhe" });
    expect(d.getAttribute("aria-modal")).toBe("true");
    expect(d.getAttribute("aria-labelledby")).toBeTruthy();
    expect(d.textContent).toContain("Conteúdo");
  });

  it("fecha com Esc", () => {
    render(<Exemplo />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("fecha clicando fora da caixa, mas não clicando dentro", () => {
    render(<Exemplo />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
    fireEvent.click(screen.getByText("Conteúdo"));
    expect(screen.getByRole("dialog")).toBeTruthy();
    fireEvent.click(screen.getByTestId("caixa-fundo"));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("fecha com o botão Fechar", () => {
    render(<Exemplo />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("o foco vai para dentro ao abrir e volta ao gatilho ao fechar", () => {
    render(<Exemplo />);
    const gatilho = screen.getByRole("button", { name: "Abrir detalhe" });
    gatilho.focus();
    fireEvent.click(gatilho);
    expect(screen.getByRole("dialog").contains(document.activeElement)).toBe(true);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(document.activeElement).toBe(gatilho);
  });

  it("o foco fica preso na caixa: Tab no último vai ao primeiro; Shift+Tab no primeiro vai ao último", () => {
    render(<Exemplo />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
    const fechar = screen.getByRole("button", { name: "Fechar" });
    const outro = screen.getByRole("button", { name: "Outro botão" });
    outro.focus();
    fireEvent.keyDown(outro, { key: "Tab" });
    expect(document.activeElement).toBe(fechar);
    fireEvent.keyDown(fechar, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(outro);
  });

  it("trava a rolagem do fundo enquanto aberta e devolve ao fechar; largura conforme o tipo de detalhe", () => {
    render(<Exemplo largo />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
    expect(document.body.style.overflow).toBe("hidden");
    expect(screen.getByRole("dialog").className).toContain("max-w-[860px]");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(document.body.style.overflow).not.toBe("hidden");
  });
});

describe("pedido 20", () => {
  it("o fundo escurecido é filho direto do body (cobre a tela inteira, acima de cabeçalho e rodapé)", () => {
    render(<Exemplo />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
    expect(screen.getByTestId("caixa-fundo").parentElement).toBe(document.body);
    expect(screen.getByTestId("caixa-fundo").className).toContain("fixed inset-0");
  });

  const ef = (fator: string, nivel: string, aj: number, fdr: boolean): EfeitoApi => ({
    fator, nivel, referencia: "y", grupo: "assistente", n_nivel: 300, n_referencia: 2000, taxa_nivel: 0.2, taxa_referencia: 0.25,
    efeito_bruto_pp: aj, bruto_ic_inf: aj - 4, bruto_ic_sup: aj + 4, efeito_ajustado_pp: aj, ajustado_ic_inf: aj - 4, ajustado_ic_sup: aj + 4,
    p_valor: 0.01, significativo_fdr: fdr, e_value: 1.2, metodo: "logit_ame", amostra_suficiente: true, leitura: null, ordem: null,
  });
  it("barra do primeiro grupo: laranja só quando o selo é 'diferença real'", () => {
    const real = prepararFloresta([ef("recusa", "sim", -16, true)], "assistente").linhas[0]!;
    const semDif = prepararFloresta([{ ...ef("modelo_familia", "gpt-4", 0.3, false), ajustado_ic_inf: -4, ajustado_ic_sup: 4 }], "assistente").linhas[0]!;
    const a = render(<DetalheFator l={real} />);
    expect(a.container.querySelector(".bg-laranja")).not.toBeNull();
    a.unmount();
    const b = render(<DetalheFator l={semDif} />);
    expect(b.container.querySelector(".bg-laranja")).toBeNull();
    expect(b.container.querySelector(".bg-violeta-claro")).not.toBeNull();
  });
});

describe("pedido 21 — saída da caixa", () => {
  it("durante a animação de saída o fundo e a caixa não pegam cliques; depois a caixa some", () => {
    vi.useFakeTimers();
    const antes = window.matchMedia;
    window.matchMedia = ((q: string) => ({ matches: false, media: q, addEventListener: () => {}, removeEventListener: () => {} })) as unknown as typeof window.matchMedia;
    try {
      render(<Exemplo />);
      fireEvent.click(screen.getByRole("button", { name: "Abrir detalhe" }));
      act(() => { vi.advanceTimersByTime(50); });
      fireEvent.keyDown(window, { key: "Escape" });
      expect(screen.getByTestId("caixa-fundo").style.pointerEvents).toBe("none");
      expect(screen.getByRole("dialog").style.pointerEvents).toBe("none");
      act(() => { vi.advanceTimersByTime(250); });
      expect(screen.queryByRole("dialog")).toBeNull();
    } finally {
      window.matchMedia = antes;
      vi.useRealTimers();
    }
  });
});
