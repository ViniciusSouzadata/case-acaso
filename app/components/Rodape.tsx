"use client";

import { useApi } from "@/lib/useApi";
import { t } from "@/lib/mensagens";

interface Saude {
  ok: boolean;
  ultimo_lote: { lote_id: number; terminado_em: string | null } | null;
  versao_definicao: string | null;
}

function dataLegivel(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? null
    : d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo" });
}

/** REQ-407: rodapé fixo com data da carga, versão da definição e fonte. */
export function Rodape() {
  const r = useApi<Saude>("/api/saude");
  const dados = r.estado === "ok" ? r.corpo.dados : null;
  const data = dataLegivel(dados?.ultimo_lote?.terminado_em);

  return (
    <footer className="fixed inset-x-0 bottom-0 z-40 border-t border-[#2a2a33] bg-tinta px-4 py-2 text-xs text-white/80">
      <div className="mx-auto flex max-w-5xl flex-wrap gap-x-4 gap-y-1">
        {r.estado === "carregando" ? <span>{t("rodape.carregando")}</span> : null}
        {r.estado === "erro" ? <span>{t("rodape.indisponivel")}</span> : null}
        {data ? <span>{t("rodape.atualizado", { data })}</span> : null}
        {dados?.versao_definicao ? <span>{t("rodape.definicao", { versao: dados.versao_definicao })}</span> : null}
        <span>{t("rodape.fonte")}</span>
      </div>
    </footer>
  );
}
