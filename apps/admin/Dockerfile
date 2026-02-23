# Build Stage
FROM node:20-slim AS builder

WORKDIR /app

# Copy root workspace configurations
COPY package*.json ./
COPY apps/admin/package*.json ./apps/admin/

# Install dependencies (handles workspaces)
RUN npm install

# Copy source code and libs
COPY apps/admin/ ./apps/admin/
# If admin depends on any libs, copy them here
# COPY libs/ ./libs/ 

WORKDIR /app/apps/admin

# Build-time API URL for Vite
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Build the app
RUN npm run build

# Runtime Stage - using unprivileged nginx for security
FROM nginxinc/nginx-unprivileged:alpine

# Copy build artifacts
COPY --from=builder /app/apps/admin/dist /usr/share/nginx/html
COPY apps/admin/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
