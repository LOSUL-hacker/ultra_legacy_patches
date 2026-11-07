#!/usr/bin/env bash
# Apply the LOSUL patchset on top of a tree synced from UPSTREAM LineageOS (no fork overrides).
# Usage: ./apply-patchset.sh [TREE_ROOT=.]      Each project gets one commit "LOSUL patchset".
set -u
ROOT=$(cd "${1:-.}" && pwd); HERE=$(cd "$(dirname "$0")" && pwd)/patches
ok=0; skip=0; fail=()
while IFS=$'\t' read -r path fork upstream branch base patch; do
  [ "$path" = path ] && continue; [ "$patch" = "-" ] && continue
  dir="$ROOT/$path"
  if [ ! -e "$dir/.git" ]; then echo "SKIP     $path (not in tree)"; skip=$((skip+1)); continue; fi
  if git -C "$dir" apply --check -R "$HERE/$patch" 2>/dev/null; then echo "DONE     $path (already applied)"; skip=$((skip+1)); continue; fi
  if ! git -C "$dir" diff --quiet || ! git -C "$dir" diff --cached --quiet; then echo "SKIP     $path (uncommitted changes)"; skip=$((skip+1)); continue; fi
  if git -C "$dir" apply --3way --index "$HERE/$patch" 2>/tmp/apply.err; then
    git -C "$dir" -c user.name="${GIT_AUTHOR_NAME:-LOSUL patchset}" -c user.email="${GIT_AUTHOR_EMAIL:-patchset@localhost}" commit -q -m "LOSUL patchset (net diff vs upstream $upstream $branch)"
    echo "APPLIED  $path"; ok=$((ok+1))
  else echo "CONFLICT $path  (resolve markers in $dir, then 'git add -A && git commit')"; fail+=("$path"); fi
done < "$HERE/MANIFEST.tsv"
echo; echo "applied: $ok  skipped: $skip  conflicts: ${#fail[@]}"; [ ${#fail[@]} -eq 0 ] || { printf '  %s\n' "${fail[@]}"; exit 1; }
