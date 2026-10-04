# Security Policy

## Never commit secret material

Do not commit:

- `audit_private.pem`
- private Ed25519 seeds
- `.key`, `.p12`, `.pfx` files
- environment files containing secrets
- workflow artifacts containing secret material

The production key must be entered only as a GitHub environment secret.

## Production signing is gated

Do not enable or create an actual production signing workflow until E1/G2 production eligibility is closed and the G6 authorization prerequisites are available.

## Public repository expectation

It is intentional that this repository is public. Public source, policy and v1.36 subject metadata are not secret. The Audit Authority private key is the protected asset.
