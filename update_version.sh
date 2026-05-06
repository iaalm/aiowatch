#!/usr/bin/env bash

set -euo pipefail

# Available options:
#   major | minor | patch | rc | alpha | beta | explicit x.y.z
number="${1:-minor}"
echo "Updating version with: ${number}"

git fetch origin

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Tracked files have uncommitted changes. Please commit/stash first."
  exit 1
fi

upstream_ref="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD || true)"
if [ -z "${upstream_ref}" ]; then
  upstream_ref="origin/main"
fi

if ! git merge-base --is-ancestor "${upstream_ref}" HEAD; then
  echo "Current branch is behind ${upstream_ref}. Please rebase/merge first."
  exit 1
fi

uvx hatch version "${number}"
v="$(uvx hatch version)"

git add aiowatch/__about__.py
git commit -m "Bump version to ${v}"

tag="v${v}"
if git rev-parse "${tag}" >/dev/null 2>&1; then
  echo "Tag ${tag} already exists."
  exit 1
fi

git tag "${tag}"
git push origin HEAD
git push origin "${tag}"

echo "Pushed commit and tag ${tag}. GitHub publish workflow should now trigger."
