#!/usr/bin/env bash
# Restage the cross-engine docs corpus for graphify.
# Copies each project's top-level docs/*.md (excluding raw chronological USER_TEST_LOG files).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
STAGE="$HERE/corpus"
rm -rf "$STAGE"
mkdir -p "$STAGE/ss2vr" "$STAGE/bioshockvr" "$STAGE/somavr"

copy_docs () {  # src_docs_dir  dst
  find "$1" -maxdepth 1 -type f -name "*.md" ! -iname "*USER_TEST_LOG*" -exec cp {} "$2/" \;
}

copy_docs "D:/Dev Debug/ss2vr-work/docs"    "$STAGE/ss2vr"
copy_docs "D:/Dev Debug/BioshockVR/docs"    "$STAGE/bioshockvr"
copy_docs "D:/Dev Debug/SOMAVR/docs"        "$STAGE/somavr"
# High-signal Bioshock engine-format notes live in a subfolder:
find "D:/Dev Debug/BioshockVR/docs/Engine Findings" -type f -name "*.md" \
  -exec cp {} "$STAGE/bioshockvr/" \; 2>/dev/null || true

echo "Staged:"
for d in ss2vr bioshockvr somavr; do
  echo "  $d: $(ls -1 "$STAGE/$d"/*.md 2>/dev/null | wc -l) files"
done
