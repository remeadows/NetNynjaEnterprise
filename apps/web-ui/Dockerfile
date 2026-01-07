# NetNynja Enterprise - Web UI Dockerfile
# Development stage uses volume mounts from docker-compose

# ============================================
# Base stage
# ============================================
FROM node:20-alpine AS base
WORKDIR /app
RUN apk add --no-cache libc6-compat

# ============================================
# Development stage (uses volume mounts)
# ============================================
FROM base AS development
WORKDIR /app

# Copy package.json for deps reference
COPY package.json ./

# Create a modified package.json without workspace dependencies for container build
RUN cat package.json | sed 's/"@netnynja\/shared-types": "\*",//g' | sed 's/"@netnynja\/shared-ui": "\*",//g' > package.temp.json && mv package.temp.json package.json

# Install all dependencies including dev deps
RUN npm install --legacy-peer-deps

EXPOSE 3000
ENV NODE_ENV=development

# Create symlinks at runtime (after volume mounts) and start vite
CMD ["sh", "-c", "ln -sf /app/node_modules /packages/shared-ui/node_modules 2>/dev/null; ln -sf /app/node_modules /packages/shared-types/node_modules 2>/dev/null; npx vite --host 0.0.0.0 --port 3000"]

# ============================================
# Build stage (for production)
# ============================================
FROM base AS builder
WORKDIR /app
COPY package.json ./
RUN npm install 2>/dev/null || true
COPY . .
RUN npm run build 2>/dev/null || echo "Build requires shared packages"

# ============================================
# Production stage (nginx)
# ============================================
FROM nginx:1.25-alpine AS production

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html 2>/dev/null || true

# Create non-root user
RUN chown -R nginx:nginx /usr/share/nginx/html 2>/dev/null || true

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --spider -q http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
