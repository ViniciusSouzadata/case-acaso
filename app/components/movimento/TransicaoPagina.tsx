"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "motion/react";
import { MOV } from "@/lib/movimento";

const Contexto = createContext<(href: string) => void>(() => undefined);

/** Para trocar de tela com saída suave: a tela atual some (fade + desfoque leve) e só então a rota muda; a tela nova entra pelas próprias peças. */
export const useNavegar = () => useContext(Contexto);

/** `cabecalho` fica fora da área que some, para a pílula do menu deslizar sem piscar. */
export function TransicaoPagina({ children, cabecalho }: { children: ReactNode; cabecalho: ReactNode }) {
  const router = useRouter();
  const reduzido = useReducedMotion() ?? false;
  const [saindo, setSaindo] = useState(false);
  // O conteúdo das telas só é montado no navegador: com o HTML do servidor o motion não retoma o desfoque/subida na hidratação e a entrada travaria no meio.
  const [montado, setMontado] = useState(false);
  useEffect(() => setMontado(true), []);

  const navegar = useCallback(
    (href: string) => {
      setSaindo(true);
      window.setTimeout(() => {
        router.push(href);
        setSaindo(false);
      }, MOV.pagina.saida * 1000);
    },
    [router],
  );

  return (
    <Contexto.Provider value={navegar}>
      <div className="mx-auto max-w-6xl px-4 pt-3">{cabecalho}</div>
      <motion.main
        className="mx-auto max-w-6xl px-4 pb-4 pt-2"
        animate={saindo ? (reduzido ? { opacity: 0 } : { opacity: 0, filter: `blur(${MOV.pagina.blurSaida}px)` }) : { opacity: 1, filter: "blur(0px)" }}
        transition={{ duration: saindo ? MOV.pagina.saida : 0, ease: MOV.curva.entrada }}
      >
        {montado ? children : null}
      </motion.main>
    </Contexto.Provider>
  );
}
