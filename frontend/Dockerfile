FROM node:24 AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ARG NUXT_PUBLIC_API_URL
ARG NUXT_PUBLIC_WEBSOCKET_SERVER_URL

RUN npm run build

FROM node:24-alpine3.21

WORKDIR /app

ENV PORT=3000

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /app/.output ./.output

USER appuser

EXPOSE $PORT

CMD sh -c "node .output/server/index.mjs"