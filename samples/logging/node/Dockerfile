FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY index.js .

# Required for trace correlation
ENV GCP_PROJECT_ID=<MY_GCP_PROJECT_ID>
ENV K_SERVICE=sample-logger-node
ENV APP_ENV=dev

CMD ["npm", "start"]
