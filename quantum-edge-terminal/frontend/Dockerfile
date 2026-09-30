FROM node:20-alpine
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
# next build needs the devDependencies (TypeScript, PostCSS, Autoprefixer); they are pruned after the build.
RUN npm ci --include=dev

COPY . .
RUN npm run build && npm prune --omit=dev

ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
