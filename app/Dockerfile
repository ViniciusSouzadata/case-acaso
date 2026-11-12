FROM node:22-slim AS dependencias
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Estágio de testes (compose, perfil "testes"): sem o build do Next; roda o vitest contra o banco do compose.
FROM dependencias AS testes
CMD ["npx", "vitest", "run"]

# Build leve (máquina de 4 GB): teto de memória do Node conservador, telemetria desligada, sem repetir o
# type-check dentro do `next build` (tsc e vitest já rodam no estágio de testes).
FROM dependencias AS construcao
ENV NEXT_TELEMETRY_DISABLED=1 NODE_OPTIONS=--max-old-space-size=1024 PULAR_TIPOS_NO_BUILD=1
RUN npm run build

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0 NEXT_TELEMETRY_DISABLED=1
COPY --from=construcao /app/.next/standalone ./
COPY --from=construcao /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
