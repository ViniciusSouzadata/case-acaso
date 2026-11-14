import { Fragment } from "react";

/** Põe em destaque (negrito e cor) o que a frase marca com [[ ]]. Os colchetes não aparecem: o texto fica igual para leitores de tela e testes. */
export function DestacaNumeros({ texto }: { texto: string }) {
  const partes = texto.split(/\[\[(.+?)\]\]/g);
  return (
    <>
      {partes.map((p, i) =>
        i % 2 === 1 ? (
          <strong key={i} className="font-semibold text-violeta-escuro">{p}</strong>
        ) : (
          <Fragment key={i}>{p}</Fragment>
        ),
      )}
    </>
  );
}
