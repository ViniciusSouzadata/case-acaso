import { t } from "@/lib/mensagens";
import { formatarInt } from "@/lib/regras";

/** REQ-404: o aviso de amostra pequena. É o único texto que explica a regra; telas e gráficos reutilizam. */
export function AvisoAmostra({ n }: { n: number | null }) {
  return (
    <p role="note" className="mt-1 rounded border border-laranja bg-amber-50 px-2 py-1 text-xs text-slate-800">
      <strong>{t("amostra.titulo")}.</strong> {t("amostra.explicacao", { n: formatarInt(n) })}
    </p>
  );
}
