#!/usr/bin/env bash
set -euo pipefail
if find . -type f \( -name '*.pem' -o -name '*.key' -o -name '*.seed' -o -name '*.p12' -o -name '*.pfx' \) -print -quit | grep -q .; then
  echo 'forbidden secret-like file found' >&2
  exit 1
fi
if grep -RIn --binary-files=without-match --exclude-dir=.git -E -- '-----BEGIN (ENCRYPTED |OPENSSH )?PRIVATE KEY-----' .; then
  echo 'private-key PEM marker found' >&2
  exit 1
fi
echo 'PUBLIC_SAFE_SCAN=PASS'
