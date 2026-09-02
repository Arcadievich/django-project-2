FROM node:16.16-slim

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY bundles-src/ ./bundles-src/
COPY assets ./assets

CMD ["npx", "parcel", "build", "bundles-src/index.js", "--dist-dir", "frontend", "--public-url", "./"]