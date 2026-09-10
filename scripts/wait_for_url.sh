#!/usr/bin/env bash
# Wait for a URL to become available
URL=${1:-http://127.0.0.1:8000/health}
RETRIES=${2:-30}
SLEEP=${3:-1}
for i in $(seq 1 $RETRIES); do
  if curl -sSf "$URL" >/dev/null 2>&1; then
    echo "OK: $URL"
    exit 0
  fi
  sleep $SLEEP
done
echo "Timeout waiting for $URL"
exit 1
