#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: tools/release.sh 2.5.1"
  exit 1
fi

if ! echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "ERROR: Version must look like 2.5.1"
  exit 1
fi

TAG="v$VERSION"

echo "===== release $VERSION ====="

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: Working tree has uncommitted changes. Commit or stash them first."
  git status --short
  exit 1
fi

git fetch origin --tags

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "ERROR: Tag $TAG already exists locally."
  exit 1
fi

if git ls-remote --tags origin "$TAG" | grep -q "$TAG"; then
  echo "ERROR: Tag $TAG already exists on origin."
  exit 1
fi

sed -i "s/ENV VERSION=\"[0-9.]*\"/ENV VERSION=\"$VERSION\"/g" Dockerfile
sed -i "s/SCRIPT VERSION [0-9.]*/SCRIPT VERSION $VERSION/g" root/scripts/download.bash

if [ -f scripts/download.bash ]; then
  sed -i "s/SCRIPT VERSION [0-9.]*/SCRIPT VERSION $VERSION/g" scripts/download.bash
fi

if [ -f README.md ]; then
  sed -i "s/ama-unraid:[0-9.][0-9.]*/ama-unraid:$VERSION/g" README.md || true
fi

echo
echo "===== changed files ====="
git status --short

git add Dockerfile root/scripts/download.bash scripts/download.bash README.md 2>/dev/null || true
git commit -m "Release AMA-Unraid $VERSION"

git tag -a "$TAG" -m "AMA-Unraid $VERSION"

git push origin master
git push origin "$TAG"

echo
echo "Release pushed: $TAG"
echo "GitHub Actions will build the Docker image and create the GitHub Release."
