# --- Stage 1: Builder (Bun) ---
# Use the official Bun image for the build environment
FROM oven/bun as builder

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and bun.lockb (if used) to leverage Docker's layer caching
COPY package.json bun.lock ./

# Install dependencies using Bun
# Replace `npm install` or `yarn install` with `bun install`
RUN bun install

# Copy the rest of the application files
COPY . .

# Run the build command for your static site generator
# This command should output your static files to a designated directory, e.g., 'dist' or 'build'
RUN bun run build

# --- Stage 2: Final (Nginx) ---
# Use a lightweight Nginx image
FROM nginx:alpine

# Copy a custom Nginx configuration file (optional, but recommended for single-page apps)
# If you need custom config, place it in an 'nginx' folder, e.g., 'nginx/default.conf'
# COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy the static assets from the 'builder' stage into the Nginx default document root
# Make sure to replace '/app/dist' with the actual output directory from your 'bun run build'
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx listens on port 80 by default
EXPOSE 80

# The default Nginx CMD will start the server
