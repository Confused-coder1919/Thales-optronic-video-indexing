FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* /app/
RUN npm install

COPY . /app

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
