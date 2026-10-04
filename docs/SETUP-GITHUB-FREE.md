# GitHub Free Setup — Option A

## Phase 1 — create the repository

Create a new **public** GitHub repository, for example:

`pgcp-audit-authority-signer`

Do not add a README, `.gitignore`, or license during creation if using the supplied repository bundle as the initial contents.

GitHub Free currently allows environments, environment secrets and deployment protection rules in public repositories. GitHub-hosted standard runners are free and unlimited for public repositories.

## Phase 2 — upload the shadow signer

Upload the repository contents from this bundle and commit them to `main`.

The only non-GitHub workflow dependency is Python plus the packages in `requirements.txt`.

## Phase 3 — protect `main`

Repository → Settings → Branches → Add branch protection rule.

Recommended minimum:

- require pull request before merge;
- require at least one approval where feasible;
- require conversation resolution;
- require status checks;
- require signed commits where supported by your workflow;
- block force pushes;
- block branch deletion.

## Phase 4 — restrict Actions

Repository → Settings → Actions → General.

Use the most restrictive available Actions policy. These supplied workflows deliberately use no third-party `uses:` actions, so there are no third-party action refs to pin in this initial bundle.

## Phase 5 — create `shadow` environment

Repository → Settings → Environments → New environment → `shadow`.

No secret is required for shadow mode.

The shadow workflow generates its own disposable key.

## Phase 6 — create `production` environment

Repository → Settings → Environments → New environment → `production`.

Configure:

- deployment branch/tag restriction: `main` only;
- required reviewer: the designated production reviewer;
- prevent self-review when a second authorized reviewer is available.

Do not add the production key yet.

## Phase 7 — run shadow validation

Run `Shadow Signer Validation`.

The required result is PASS. The shadow public key must explicitly differ from the v1.36 root. No production private key is involved.

## Phase 8 — add the historical key

Only after the repository, branch protections, Actions restrictions and production environment protections are configured should the existing historical fixture be placed into the production secret.

Recommended secret name:

`AUDIT_AUTHORITY_KEY_PEM_B64`

The secret value must be the base64 encoding of the exact historical PEM file. Base64 is only transport encoding; GitHub's secret mechanism provides the protected-secret storage.

### Windows PowerShell transfer pattern

From the machine where the historical fixture is legitimately held:

```powershell
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes('PATH\\TO\\audit_private.pem'))
$b64 | gh secret set AUDIT_AUTHORITY_KEY_PEM_B64 --env production --repo OWNER/pgcp-audit-authority-signer
Remove-Variable b64
```

Do not echo `$b64`, display the PEM contents, or commit the key.

## Phase 9 — custody verification

Manually dispatch `Verify Production Custody`.

Approve the protected `production` environment deployment when prompted.

Expected public-only result:

- `result = PASS`
- `public_key_match = true`
- derived public key equals the fixed v1.36 root
- no private-key material in result

This closes only the custody-identity evidence aspect. It does not by itself close all PKE controls.

## Phase 10 — do not sign yet

After custody verification, stop and assemble the formal E1/G2 evidence record.

Real v1.36 signing remains blocked until all PKE-01 through PKE-08 controls and the later G6 prerequisites are satisfied.
