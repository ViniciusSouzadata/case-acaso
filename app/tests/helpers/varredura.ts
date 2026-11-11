// Detector de dado sensível em respostas da API (princípio 1: nada de hashed_ip, user-agent nem texto de conversa).

const CHAVES_PROIBIDAS =
  /^(hashed_ip|ip|user_?agent|ua|ua_familia|usuario_id|usuario_id_ip|usuario_id_ip_ua|conversa_id|conversation_hash|turn_identifier|prompt|pergunta|resposta|mensagem|mensagens|conteudo|content|texto|texto_conversa|input|output|turno|turnos_texto|header)$/i;

const VALORES_PROIBIDOS: [string, RegExp][] = [
  ["hash hexadecimal longo (cara de hashed_ip ou id de usuário)", /\b[0-9a-f]{32,}\b/i],
  ["user-agent de navegador", /Mozilla\/\d|AppleWebKit\/|Gecko\/\d|\bChrome\/\d|\bSafari\/\d|\bEdg\/\d/],
  ["endereço IPv4", /\b(?:\d{1,3}\.){3}\d{1,3}\b/],
  ["endereço IPv6", /\b(?:[0-9a-f]{1,4}:){4,7}[0-9a-f]{1,4}\b/i],
];

export interface Achado {
  caminho: string;
  motivo: string;
}

/** Percorre o JSON inteiro e lista tudo que tem chave ou valor com cara de dado pessoal ou de conversa. */
export function varrer(valor: unknown, caminho = "$"): Achado[] {
  const achados: Achado[] = [];
  if (typeof valor === "string") {
    for (const [motivo, re] of VALORES_PROIBIDOS) if (re.test(valor)) achados.push({ caminho, motivo });
  } else if (Array.isArray(valor)) {
    valor.forEach((v, i) => achados.push(...varrer(v, `${caminho}[${i}]`)));
  } else if (valor && typeof valor === "object") {
    for (const [k, v] of Object.entries(valor as Record<string, unknown>)) {
      if (CHAVES_PROIBIDAS.test(k)) achados.push({ caminho: `${caminho}.${k}`, motivo: "chave proibida" });
      achados.push(...varrer(v, `${caminho}.${k}`));
    }
  }
  return achados;
}
