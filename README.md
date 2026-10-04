# PGCP Audit Authority — GitHub Free / Option A Shadow Signer

This repository is a GitHub-ready implementation vessel for the governed strategy:

- key strategy: `OPTION_A_SAME_HISTORICAL_KEY`
- custody path: `PATH_B_NEW_AUTHORIZED_EXTERNAL_CUSTODY`
- v1.36 trust-root: unchanged
- production key replacement: prohibited
- trust-root rotation: prohibited under this path

The repository is intentionally public-safe: no private key is stored in source control. The current workflows use only shell commands and the repository source; no third-party GitHub Actions are required for the shadow or custody-verification path.

## Security boundary

The historical private key is intended to exist only as a protected GitHub **production environment secret**. The repository contains only public subject data, policy, signer source, tests and workflows.

The production workflow is a custody-verification workflow at this stage. It does **not** issue the real v1.36 disposition. Real signing remains blocked until the formal E1/G2 eligibility record is closed and the later G6 prerequisites are available.

The signer does not expose a generic `sign(bytes)` interface. It recognizes only the governed `issue_audit_disposition` operation and exact v1.36 subject.

## Fixed v1.36 subject

See `config/v1.36-authorized-subject.json`. This file contains public/non-secret identity values only.

## Shadow phase

`shadow.yml` generates an ephemeral synthetic Ed25519 key and exercises the restricted signer. The synthetic key is deliberately required to differ from the v1.36 root. Shadow success is not production eligibility evidence.

## Production custody phase

`verify-production-custody.yml` references the GitHub `production` environment. It consumes `AUDIT_AUTHORITY_KEY_PEM_B64` only after the environment's protection rules permit the job to start.

The workflow derives the public key inside the runner and compares it to the exact v1.36 root. It emits public-only verification evidence.

## Important implementation note

This GitHub-only construction does not yet provide the full durable issuance ledger required by the PGCP production signing design. Therefore it is suitable for custody qualification, not yet sufficient by itself for G6 production signing. A durable, fail-closed issuance ledger remains a separate prerequisite before the first real signature.
