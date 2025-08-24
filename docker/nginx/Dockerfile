FROM nginx:alpine

# Install certbot for SSL certificate management
RUN apk add --no-cache certbot certbot-nginx openssl

# Create necessary directories
RUN mkdir -p /var/log/nginx /etc/ssl/certs /var/www/certbot

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose ports
EXPOSE 80 443

# Use custom startup script
CMD ["/start.sh"]
