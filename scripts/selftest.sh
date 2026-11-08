#!/usr/bin/env bash
# Full local verification loop: unit tests -> self-audit -> build -> install smoke test.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"

echo "[1/5] unit tests"
"$PY" -m unittest discover -s tests -v

echo "[2/5] self-audit (three-language README parity)"
"$PY" -m docconcord check . --format text --fail-on error

echo "[3/5] report formats + deterministic output"
"$PY" -m docconcord check . --format json > /tmp/docconcord-report.json
"$PY" -m docconcord check . --format junit > /tmp/docconcord-report.xml
"$PY" -m docconcord check . --format markdown > /tmp/docconcord-report.md
"$PY" -c "import json;d=json.load(open('/tmp/docconcord-report.json'));assert d['summary']['errors']==0;print('JSON summary OK:',d['summary'])"
"$PY" -c "import xml.etree.ElementTree as E;E.parse('/tmp/docconcord-report.xml');print('JUnit XML OK')"

echo "[4/5] build wheel + sdist"
bash scripts/build.sh > /tmp/docconcord-build.log
ls -l dist

echo "[5/5] install artifact into a clean venv and smoke-test the CLI"
# A leaked PYTHONPATH makes venv's pip resolve the source tree instead of the
# installed artifact, so drop it for the isolated smoke test.
unset PYTHONPATH
VENV="$(mktemp -d)/venv"
"$PY" -m venv "$VENV"
"$VENV/bin/python" -m pip install --no-deps --quiet dist/*.whl
"$VENV/bin/docconcord" version
"$VENV/bin/docconcord" rules | head -5
"$VENV/bin/python" -m docconcord check . --format text --fail-on error
rm -rf "$VENV"

echo "ALL CHECKS PASSED"
