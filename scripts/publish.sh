#!/usr/bin/env bash
# Publishes ONLY the source code in this repository. Never store user records here.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v gh >/dev/null; then
  echo 'Chybí GitHub CLI (gh). Nainstaluj gh a spusť gh auth login.' >&2
  exit 1
fi
if ! command -v git >/dev/null; then
  echo 'Chybí git.' >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo 'Nejdřív se přihlas: gh auth login' >&2
  exit 1
fi
user="$(gh api user --jq '.login')"
if [[ "$user" != 'sparesparrow' ]]; then
  echo "Přihlášený GitHub uživatel je '$user', očekává se 'sparesparrow'." >&2
  exit 1
fi
if [[ -e .env || -e .env.local ]]; then
  echo 'Bezpečnost: ve složce je lokální .env. Před publikováním ji zkontroluj nebo odstraň.' >&2
  exit 1
fi
read -r -p 'Vytvořím VEŘEJNÝ repozitář sparesparrow/omarchy-cz-egovernment. Napiš ANO: ' answer
if [[ "$answer" != 'ANO' ]]; then
  echo 'Zrušeno.'
  exit 0
fi
if [[ ! -d .git ]]; then
  git init -b main
fi
# Avoid accidentally uploading data outside the tracked source distribution.
git add .gitignore .github README.md LICENSE manifest.json Egovernment.qml agents scripts/publish.sh tests
if ! git diff --cached --quiet; then
  git commit -m 'Initial Czech eGovernment Omarchy plugin and agent skill'
fi
gh repo create sparesparrow/omarchy-cz-egovernment --public --source=. --remote=origin --push
printf '\nPublikováno: https://github.com/sparesparrow/omarchy-cz-egovernment\n'
