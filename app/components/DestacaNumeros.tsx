import { Fragment } from "react";

/** Põe em destaque (negrito e cor) os números de uma frase-resposta. O texto continua o mesmo para leitores de tela e testes. */
export function DestacaNumeros({ texto }: { texto: string }) {
  const partes = texto.split(/(\d+(?:[.,]\d+)*(?:\s?%)?)/g);
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
