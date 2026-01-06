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

# Install dependencies (shared packages will be mounted)
RUN npm install 2>/dev/null || true

EXPOSE 5173
ENV NODE_ENV=development

# Source will be mounted as volume in docker-compose
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

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
