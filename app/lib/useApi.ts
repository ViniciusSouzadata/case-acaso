"use client";

import { useEffect, useState } from "react";

// Tipos locais (não importar lib/api.ts aqui: ele usa módulos de servidor).
export interface MetaCliente {
  versao_definicao: string | null;
  versao_analise: string | null;
  atualizado_em: string | null;
  lote_id: number | null;
  request_id: string;
  fonte: string;
  [extra: string]: unknown;
}

export interface CorpoApi<T> {
  dados: T;
  meta: MetaCliente;
}

export type EstadoApi<T> =
  | { estado: "carregando" }
  | { estado: "ok"; corpo: CorpoApi<T> }
  | { estado: "erro"; mensagem: string; requestId: string | null };

/** REQ-401: as telas só falam com a API. Devolve carregando, ok ou erro (com request_id). */
export function useApi<T>(url: string | null): EstadoApi<T> {
  const [estado, setEstado] = useState<EstadoApi<T>>({ estado: "carregando" });

  useEffect(() => {
    if (url === null) return;
    let cancelado = false;
    setEstado({ estado: "carregando" });
    fetch(url)
      .then(async (r) => {
        const json = (await r.json()) as { erro?: { mensagem: string; request_id: string } } & Partial<CorpoApi<T>>;
        if (cancelado) return;
        if (!r.ok || json.erro) {
          setEstado({
            estado: "erro",
            mensagem: json.erro?.mensagem ?? `Erro ${r.status}`,
            requestId: json.erro?.request_id ?? null,
          });
        } else {
          setEstado({ estado: "ok", corpo: json as CorpoApi<T> });
        }
      })
      .catch(() => {
        if (!cancelado) setEstado({ estado: "erro", mensagem: "Sem resposta do servidor.", requestId: null });
      });
    return () => {
      cancelado = true;
    };
  }, [url]);

  return estado;
}
