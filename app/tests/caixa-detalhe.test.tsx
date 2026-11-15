// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { CaixaDetalhe } from "@/components/CaixaDetalhe";

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
