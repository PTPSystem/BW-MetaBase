#!/bin/sh

# Start nginx in background
nginx

# Function to obtain SSL certificate
obtain_certificate() {
    local domain=$1
    local email=$2
    local staging_flag=""
    
    if [ "$CERTBOT_STAGING" = "true" ]; then
        staging_flag="--staging"
    fi
    
    echo "Obtaining SSL certificate for $domain..."
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $email \
        --agree-tos \
        --no-eff-email \
        $staging_flag \
        -d $domain
        
    if [ $? -eq 0 ]; then
        echo "Certificate obtained successfully for $domain"
        return 0
    else
        echo "Failed to obtain certificate for $domain"
        return 1
    fi
}

# Function to generate self-signed certificate as fallback
generate_self_signed() {
    local domain=$1
    echo "Generating self-signed certificate for $domain..."
    
    mkdir -p /etc/ssl/certs/$domain
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/certs/$domain/privkey.pem \
        -out /etc/ssl/certs/$domain/fullchain.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=$domain"
}

# Wait for nginx to start
sleep 5

# Check if certificates exist, if not generate them
METABASE_DOMAIN=${DOMAIN_METABASE:-StoreMgnt.Beachwood.me}
EXISTING_DOMAIN=${DOMAIN_EXISTING:-str.ptpsystem.com}
EMAIL=${SSL_EMAIL:-admin@beachwood.me}

# For Metabase domain
if [ ! -f "/etc/letsencrypt/live/$METABASE_DOMAIN/fullchain.pem" ]; then
    if ! obtain_certificate $METABASE_DOMAIN $EMAIL; then
        generate_self_signed $METABASE_DOMAIN
    fi
fi

# For existing domain (if different)
if [ "$EXISTING_DOMAIN" != "$METABASE_DOMAIN" ] && [ ! -f "/etc/letsencrypt/live/$EXISTING_DOMAIN/fullchain.pem" ]; then
    if ! obtain_certificate $EXISTING_DOMAIN $EMAIL; then
        generate_self_signed $EXISTING_DOMAIN
    fi
fi

# Reload nginx to use new certificates
nginx -s reload

# Set up certificate renewal cron job
echo "0 12 * * * /usr/bin/certbot renew --quiet && nginx -s reload" | crontab -

# Start cron daemon
crond

# Keep container running and monitor nginx
while true; do
    if ! pgrep nginx > /dev/null; then
        echo "Nginx stopped, restarting..."
        nginx
    fi
    sleep 30
done
