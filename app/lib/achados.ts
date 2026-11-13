// Apresentação dos cartões de achados (função pura): o texto vem de resultado.achado e não é reescrito, só dividido.

/** Separa o texto em frases (ponto final seguido de maiúscula; números como "2.372" e "5,6%" não quebram). */
export function frases(texto: string): string[] {
  return texto.split(/(?<=[.!?])\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ"“(])/u).map((f) => f.trim()).filter(Boolean);
}

/** As primeiras `max` frases ficam à vista; o resto vai para o recolhível "ver detalhes". */
export function resumir(texto: string, max = 2): { visivel: string; resto: string } {
  const f = frases(texto);
  return { visivel: f.slice(0, max).join(" "), resto: f.slice(max).join(" ") };
}
