# Build Stage
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
# Copy workspace config if any (assuming standalone for now based on package.json view)
# If root package.json exists, we might need it, but let's assume monorepo needs distinct install for now or copy all.
# Given complexity, let's copy everything needed for admin. (Reviewing structure again might be needed but let's start simple)
COPY apps/admin/package.json ./apps/admin/

# Install dependencies
# We need to install from root if it's a monorepo workspace.
# For now, let's assume we can build admin in isolation or copy root context.
# Best practice for monorepo Dockerfile: Context is Root.
COPY package.json package-lock.json ./
COPY apps/admin ./apps/admin

RUN npm ci
WORKDIR /app/apps/admin
RUN npm run build

# Runtime Stage
FROM nginx:alpine

COPY --from=builder /app/apps/admin/dist /usr/share/nginx/html
COPY apps/admin/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
