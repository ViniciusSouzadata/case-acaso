import { t } from "@/lib/mensagens";

export type TipoEstado = "carregando" | "vazio" | "erro";

/** REQ-410: carregando, vazio e erro (com request_id) em um só componente. */
export function Estado({
  tipo,
  mensagem,
  requestId,
}: {
  tipo: TipoEstado;
  mensagem?: string;
  requestId?: string | null;
}) {
  if (tipo === "carregando") {
    return (
      <div role="status" className="esqueleto my-2 min-h-24 w-full">
        <span className="sr-only">{t("estado.carregando")}</span>
      </div>
    );
  }
  if (tipo === "vazio") {
    return (
      <p role="status" className="py-6 text-sm text-slate-600">
        {mensagem ?? t("estado.vazio")}
      </p>
    );
  }
  return (
    <div role="alert" className="rounded border border-vermelho bg-red-50 p-4 text-sm text-slate-800">
      <p className="font-medium">{t("estado.erro")}</p>
      {mensagem ? <p className="mt-1">{mensagem}</p> : null}
      {requestId ? <p className="mt-1 text-xs text-slate-600">{t("estado.codigoErro", { requestId })}</p> : null}
    </div>
  );
}
