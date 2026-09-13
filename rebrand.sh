#!/usr/bin/env bash
# Rebrand the repo: Jarvis -> Altron, developer name -> Abbas.
# Run once from the root of the repo:   bash rebrand.sh
set -e

echo "Rebranding to Altron (developer: Abbas)..."

# 1. Text inside files
grep -rl --binary-files=without-match -e JARVIS -e Jarvis -e jarvis . \
  --exclude-dir=.git --exclude-dir=bin --exclude-dir=.buildozer \
  --exclude=rebrand.sh | while read -r f; do
    sed -i \
      -e 's/JARVIS/ALTRON/g' \
      -e 's/Jarvis/Altron/g' \
      -e 's/jarvis/altron/g' \
      -e 's/Mark Frencer Lozada/Abbas/g' \
      -e 's/MarkFrencerLozada/Abbas/g' \
      "$f"
    echo "  updated $f"
done

# 2. File names
for f in $(ls | grep -i jarvis); do
  new=$(echo "$f" | sed -e 's/JARVIS/ALTRON/g' -e 's/Jarvis/Altron/g' -e 's/jarvis/altron/g')
  git mv "$f" "$new" 2>/dev/null || mv "$f" "$new"
  echo "  renamed $f -> $new"
done

echo "Done. Review with: git status && git diff"
