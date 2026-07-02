#!/bin/bash
# Send test email using swaks (SMTP Swiss Army Knife)

if [ -z "$GMAIL_APP_PASSWORD" ]; then
  echo "Error: GMAIL_APP_PASSWORD is not set. See .env.example." >&2
  exit 1
fi

EMAIL_FROM="${EMAIL_FROM:-zan@impactquadrant.info}"
EMAIL_TO="${EMAIL_TO:-sam@cubiczan.com}"

echo "Testing email configuration for $EMAIL_FROM"
echo "Sending to: $EMAIL_TO"

swaks --to "$EMAIL_TO" \
      --from "$EMAIL_FROM" \
      --server smtp.gmail.com:587 \
      --tls \
      --auth-user "$EMAIL_FROM" \
      --auth-password "$GMAIL_APP_PASSWORD" \
      --header "Subject: Test Email from OpenClaw" \
      --body "Hello! This is a test email from OpenClaw. If you received this, email is configured correctly!" 2>&1
