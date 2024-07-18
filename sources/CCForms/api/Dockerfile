FROM node:22

WORKDIR /app

COPY package.json /app
COPY package-lock.json /app

RUN npm ci

COPY . /app

CMD ["node", "server.mjs"]
