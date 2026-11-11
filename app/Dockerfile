FROM node:22-slim AS dependencias
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Estágio de testes (compose, perfil "testes"): sem o build do Next; roda o vitest contra o banco do compose.
FROM dependencias AS testes
CMD ["npx", "vitest", "run"]

FROM dependencias AS construcao
RUN npm run build

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0
COPY --from=construcao /app/.next/standalone ./
COPY --from=construcao /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
