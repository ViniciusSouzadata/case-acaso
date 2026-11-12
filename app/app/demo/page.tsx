"use client";

import { Estado } from "@/components/Estado";
import { Numero } from "@/components/Numero";
import { t } from "@/lib/mensagens";
import { useApi } from "@/lib/useApi";

interface Resumo {
  usuarios: number;
  voltaram_7d: number;
  taxa: number;
  ic_inf: number;
  ic_sup: number;
}

/** Página de demonstração (T-401): o componente Numero nos estados normal, amostra pequena, imatura e erro. */
export default function Demo() {
  const resumo = useApi<Resumo>("/api/retencao/resumo");
  const quebrado = useApi<unknown>("/api/retencao/resumo?pais=Argentina");

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{t("demo.titulo")}</h1>
      <div className="grid gap-4 sm:grid-cols-2">
        <section aria-label={t("demo.normal")}>
          <h2 className="mb-1 text-sm font-medium">{t("demo.normal")}</h2>
          {resumo.estado === "carregando" ? <Estado tipo="carregando" /> : null}
          {resumo.estado === "erro" ? <Estado tipo="erro" mensagem={resumo.mensagem} requestId={resumo.requestId} /> : null}
          {resumo.estado === "ok" && resumo.corpo.dados ? (
            <Numero
              rotulo="Taxa de retorno em 7 dias"
              valor={resumo.corpo.dados.taxa}
              formato="pct"
              icInf={resumo.corpo.dados.ic_inf}
              icSup={resumo.corpo.dados.ic_sup}
              n={resumo.corpo.dados.usuarios}
              indicador="taxa_retorno_7d"
            />
          ) : null}
        </section>

        <section aria-label={t("demo.pequena")}>
          <h2 className="mb-1 text-sm font-medium">{t("demo.pequena")}</h2>
          <Numero rotulo="Taxa de retorno em 7 dias" valor={0.1667} formato="pct" icInf={0.06} icSup={0.4} n={12} amostraSuficiente={false} indicador="taxa_retorno_7d" />
        </section>

        <section aria-label={t("demo.imatura")}>
          <h2 className="mb-1 text-sm font-medium">{t("demo.imatura")}</h2>
          <Numero rotulo="Taxa de retorno em 7 dias" valor={null} formato="pct" n={20} madura={false} />
        </section>

        <section aria-label={t("demo.erro")}>
          <h2 className="mb-1 text-sm font-medium">{t("demo.erro")}</h2>
          {quebrado.estado === "carregando" ? <Estado tipo="carregando" /> : null}
          {quebrado.estado === "erro" ? <Estado tipo="erro" mensagem={quebrado.mensagem} requestId={quebrado.requestId} /> : null}
        </section>
      </div>
    </div>
  );
}
