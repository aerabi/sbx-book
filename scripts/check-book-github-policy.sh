#!/bin/sh
# Evaluate policy only. Never send these requests to GitHub.
set -eu
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 SANDBOX_NAME (run on the host)" >&2
  exit 2
fi
command -v sbx >/dev/null 2>&1 || {
  echo "sbx is required on the host; no policy checks were run." >&2
  exit 1
}
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sbx policy ls "$1" --wide
while IFS="$(printf '\t')" read -r expected method url; do
  printf '\nExpected %s: %s %s\n' "$expected" "$method" "$url"
  if sbx policy check http --sandbox "$1" --method "$method" "$url"; then
    :
  else
    printf 'CLI exited nonzero; review the output above before continuing.\n'
  fi
done < "$repo_root/kits/book-github/policy-cases.tsv"
printf '\nExpected deny: unrelated network destination\n'
sbx policy check network --sandbox "$1" example.com:443
printf '\nCompare every decision above with its expectation before adding credentials.\n'
printf 'This script records CLI output; it does not infer pass/fail from exit codes.\n'
