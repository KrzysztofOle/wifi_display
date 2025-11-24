#!/usr/bin/env bash
set -euo pipefail

# Użycie:
#   ./safe_temp_branch.sh              → utworzy gałąź temp/YYYY-MM-DD
#   ./safe_temp_branch.sh temp/2025-11-24  → utworzy dokładnie temp/2025-11-24
#
# Skrypt:
# - sprawdza, czy jesteś w repo git
# - sprawdza, czy gałąź już nie istnieje (lokalnie / na origin)
# - tworzy nową gałąź i przełącza na nią
# - commit-uje wszystkie bieżące zmiany (git add -A)
# - wypycha gałąź na origin i ustawia tracking

BRANCH_NAME="${1:-temp/$(date +%F)}"

echo "== Tworzenie gałęzi '$BRANCH_NAME' i przenoszenie aktualnego stanu =="

# 1. Sprawdzenie, czy jesteśmy w repozytorium git
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Ten katalog nie jest repozytorium git."
  exit 1
fi

# 2. Informacja o aktualnej gałęzi
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "Aktualna gałąź: $CURRENT_BRANCH"

# 3. Sprawdzenie, czy gałąź nie istnieje lokalnie
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  echo "❌ Gałąź '$BRANCH_NAME' już istnieje lokalnie. Przerywam."
  exit 1
fi

# 4. Sprawdzenie, czy gałąź nie istnieje na origin
if git ls-remote --exit-code --heads origin "$BRANCH_NAME" >/dev/null 2>&1; then
  echo "❌ Gałąź '$BRANCH_NAME' już istnieje na origin. Przerywam."
  exit 1
fi

# 5. Utworzenie nowej gałęzi i przełączenie na nią
echo "== Przełączam na nową gałąź '$BRANCH_NAME' =="
git switch -c "$BRANCH_NAME"

# 6. Commit wszystkich aktualnych zmian (jeśli są)
if [[ -n "$(git status --porcelain)" ]]; then
  echo "== Dodaję wszystkie aktualne zmiany (git add -A) =="
  git add -A

  echo "== Tworzę commit z aktualnymi zmianami =="
  git commit -m "chore: backup stanu na $(date '+%Y-%m-%d %H:%M:%S')"
else
  echo "Brak lokalnych zmian do commita – gałąź wskazuje na bieżący commit."
fi

# 7. Wypchnięcie na origin
echo "== Wypycham gałąź '$BRANCH_NAME' na origin =="
git push -u origin "$BRANCH_NAME"

echo "✅ Gotowe. Jesteś na gałęzi: $(git rev-parse --abbrev-ref HEAD)"
