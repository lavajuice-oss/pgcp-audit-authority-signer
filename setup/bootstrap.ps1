# Run locally after creating an empty PUBLIC GitHub repository.
# This script intentionally does not set the production secret.
param(
  [Parameter(Mandatory=$true)][string]$Repo
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is required' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI (gh) is required' }

gh auth status | Out-Host

git init
git branch -M main
git add .
git commit -m 'Initialize PGCP Audit Authority Option A shadow signer'
git remote add origin "https://github.com/$Repo.git"
git push -u origin main

Write-Host "Repository pushed: https://github.com/$Repo"
Write-Host "NEXT: configure branch protection + shadow/production environments in GitHub Settings."
Write-Host "DO NOT set the production secret until those protections are complete."
