// Cache em memória por (endpoint, parâmetros, lote_id) com TTL (REQ-306).
// Lote novo muda a chave, então o cache antigo nunca é servido; as entradas velhas expiram pelo TTL ou são varridas.

export const TTL_PADRAO_MS = 60 * 60 * 1000; // 1 h

interface Entrada<T> {
  valor: T;
  expiraEm: number;
}

export class CacheTTL<T> {
  private mapa = new Map<string, Entrada<T>>();

  constructor(
    private ttlMs: number = TTL_PADRAO_MS,
    private agora: () => number = Date.now,
    private maxEntradas = 500,
  ) {}

  static chave(endpoint: string, params: Record<string, string>, loteId: number | null): string {
    const ordenados = Object.keys(params)
      .sort()
      .map((k) => `${k}=${params[k]}`)
      .join("&");
    return `${endpoint}?${ordenados}#lote=${loteId ?? "nenhum"}`;
  }

  obter(chave: string): T | undefined {
    const e = this.mapa.get(chave);
    if (!e) return undefined;
    if (e.expiraEm <= this.agora()) {
      this.mapa.delete(chave);
      return undefined;
    }
    return e.valor;
  }

  guardar(chave: string, valor: T): void {
    if (this.mapa.size >= this.maxEntradas) this.varrer();
    if (this.mapa.size >= this.maxEntradas) {
      const primeira = this.mapa.keys().next().value;
      if (primeira !== undefined) this.mapa.delete(primeira);
    }
    this.mapa.set(chave, { valor, expiraEm: this.agora() + this.ttlMs });
  }

  /** Remove o que já expirou. */
  varrer(): void {
    const t = this.agora();
    for (const [k, e] of this.mapa) if (e.expiraEm <= t) this.mapa.delete(k);
  }

  limpar(): void {
    this.mapa.clear();
  }

  get tamanho(): number {
    return this.mapa.size;
  }
}
