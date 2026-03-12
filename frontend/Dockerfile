# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

FROM node:22-alpine

WORKDIR /app

COPY package.json ./
COPY tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts index.html ./
COPY public ./public
COPY src ./src

RUN npm install
RUN npm run build

EXPOSE 4173

CMD ["npm", "run", "preview"]