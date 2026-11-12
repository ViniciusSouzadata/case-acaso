import type { NextConfig } from "next";

const config: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // só no build da imagem (Dockerfile): o type-check já é feito por `tsc --noEmit` e pelo estágio de testes
  typescript: { ignoreBuildErrors: process.env.PULAR_TIPOS_NO_BUILD === "1" },
};

export default config;
