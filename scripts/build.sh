#!/usr/bin/env bash
# Cross-platform (POSIX) one-shot build: wheel + sdist + SHA256SUMS.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"

echo "==> cleaning previous artifacts"
rm -rf build dist src/*.egg-info

echo "==> building wheel (no network, no build isolation)"
"$PY" -m pip wheel . --no-deps --no-build-isolation -w dist

echo "==> building sdist"
if "$PY" -c 'import build' >/dev/null 2>&1; then
  "$PY" -m build --sdist --no-isolation -o dist
else
  "$PY" setup.py sdist --dist-dir dist
fi

echo "==> writing SHA256SUMS"
(
  cd dist
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum *.whl *.tar.gz > SHA256SUMS
  else
    shasum -a 256 *.whl *.tar.gz > SHA256SUMS
  fi
)

echo "==> build complete"
ls -l dist
