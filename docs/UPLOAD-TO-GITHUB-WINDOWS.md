# Upload the bundle to the empty GitHub repository (Windows)

Target repository: `https://github.com/lavajuice-oss/pgcp-audit-authority-signer`

## Important

- Download and extract the ZIP. **Do not upload the ZIP itself.**
- Open the extracted project root: the folder that directly contains `README.md`, `.gitignore`, `.github`, `config`, `docs`, `policy`, `setup`, `src`, and `tests`.
- Do not copy `audit_private.pem`, any `.pem`, `.key`, `.seed`, `.p12`, `.pfx`, or any other secret into this folder.
- Do not create the production GitHub secret yet.

## Steps

1. Download `pgcp-audit-authority-github-free-optiona-v0.1-clean.zip` and choose **Extract All** in Windows File Explorer.
2. Open the extracted `pgcp-audit-authority-github-free-optiona-v0.1` folder. Confirm `README.md` is visible and `.github` exists. If you see another nested folder with the same name, open that inner folder instead.
3. Click File Explorer's address bar, type `powershell`, and press Enter. A PowerShell window should open at the project root.
4. Check Git is installed:

   ```powershell
   git --version
   ```

   If not found, install Git for Windows from `https://git-scm.com/download/win`, then reopen PowerShell in this project root.

5. Run the public-safe scan:

   ```powershell
   bash setup/check-public-safe.sh
   ```

   If `bash` is not available, skip this command for now; the CI workflow runs the tests. The scan must report `PUBLIC_SAFE_SCAN=PASS` when run in Git Bash.

6. Check for secret-like files (the expected result is no output):

   ```powershell
   Get-ChildItem -Recurse -File | Where-Object { $_.Name -match '\.(pem|key|seed|p12|pfx)$' }
   ```

7. Initialize and commit the supplied public-only files:

   ```powershell
   git init -b main
   git add .
   git status --short
   ```

   Inspect the status. It should list the supplied source, tests, public configuration, documentation, and workflows. It must not list the historical private key or any secret.

8. Commit and connect the existing empty repository:

   ```powershell
   git commit -m "Initialize PGCP Audit Authority Option A shadow signer"
   git remote add origin https://github.com/lavajuice-oss/pgcp-audit-authority-signer.git
   git push -u origin main
   ```

   Git may open a browser for GitHub authentication. Authenticate as the account that owns the repository. Do not place a personal access token directly in a command or file.

9. Refresh the repository page. You should see `.github/workflows`, `config`, `docs`, `policy`, `setup`, `src`, `tests`, and the root files.

10. In GitHub, open **Actions → Shadow Signer Validation → Run workflow**. Run only the shadow workflow at this stage. Expected outcome: PASS. It uses a disposable synthetic key and must not receive the historical production key.

## Stop condition

Stop after the shadow workflow passes and before adding any production secret. Next configure the repository protections and the `shadow`/`production` environments, then review the custody controls. The historical key is transferred only in a later explicitly authorized step.
