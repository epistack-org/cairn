#!/usr/bin/env bash
# clean-room-verify.sh — prove the "fresh machine -> running process in ~5 min" claim.
#
# Spins up a fresh python:3.12-slim container (nothing else on it), makes the CURRENT
# committed tree available as a REAL `git clone` source (via a git bundle), then runs the
# exact README "Run it" block end to end and times the wall clock.
#
# Needs only docker + git on the host. Nothing is installed on the host.
#   usage:  scripts/clean-room-verify.sh
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

git -C "$REPO_ROOT" bundle create "$WORK/cairn.bundle" "$BRANCH" >/dev/null 2>&1

cat > "$WORK/run.sh" <<INNER
#!/usr/bin/env bash
set -u
hr(){ printf '%s\n' "------------------------------------------------------------------"; }

echo "############################################################"
echo "# FRESH MACHINE  (docker: python:3.12-slim, nothing added) #"
echo "############################################################"
echo "\\\$ python3 --version"; python3 --version
echo "\\\$ which uv"; which uv || echo "uv: command not found   (NOT a prerequisite -> run block must not need it)"
echo "\\\$ which git"; which git || echo "git: not in base image -> installing (a judge's real machine has git)"
hr
APT0=\$(date +%s); apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq git >/dev/null 2>&1; APT1=\$(date +%s)
echo "\\\$ git --version"; git --version
echo "(base-image git install: \$((APT1-APT0))s -- container overhead, NOT in the run-block clock)"
hr
echo ">>> START WALL CLOCK  (git clone -> passing demo)"; T0=\$(date +%s)
set -e
echo; echo "\\\$ git clone -b $BRANCH /seed/cairn.bundle cairn"
git clone -q -b $BRANCH /seed/cairn.bundle cairn; cd cairn; echo "cloned at \$(git rev-parse --short HEAD)"
echo; echo "\\\$ python3 -m venv .venv && .venv/bin/pip install -e . pytest"
python3 -m venv .venv; .venv/bin/pip install -q --disable-pip-version-check -e . pytest
echo; echo "\\\$ .venv/bin/python fixtures/build_fixtures.py"; .venv/bin/python fixtures/build_fixtures.py >/dev/null && echo "  fixtures minted OK"
echo; echo "\\\$ .venv/bin/python -m pytest -q"; .venv/bin/python -m pytest -q
echo; echo "\\\$ .venv/bin/python demo/worked_examples.py"; .venv/bin/python demo/worked_examples.py
set +e
echo; echo "\\\$ .venv/bin/cairn ground 'fixtures/*.json'"; .venv/bin/cairn ground 'fixtures/*.json' >/dev/null; echo "  exit=\$?  (0 == all spans resolve)"
echo; echo "\\\$ .venv/bin/cairn assess assessment/runs/heterogeneous.json --battery assessment/probes.json"; .venv/bin/cairn assess assessment/runs/heterogeneous.json --battery assessment/probes.json >/dev/null; echo "  exit=\$?"
echo; echo "\\\$ .venv/bin/cairn frechet <covid trio + worobey>"; .venv/bin/cairn frechet fixtures/claim-geographic-clustering.json fixtures/claim-environmental-sampling.json fixtures/claim-live-mammal-sales.json fixtures/src-worobey-2022.json >/dev/null; echo "  exit=\$?  (2 == refuse-to-combine-as-point)"
echo; echo "\\\$ .venv/bin/cairn headtohead 'fixtures/*.json'"; .venv/bin/cairn headtohead 'fixtures/*.json' >/dev/null; echo "  exit=\$?  (2 == delta demonstrated)"
echo; echo "\\\$ .venv/bin/cairn intersect ... eggs trio"; .venv/bin/cairn intersect 'fixtures/*.json' --claims \$(.venv/bin/python -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-eggs-rong-no-association','claim-eggs-godos-no-association','claim-eggs-drouin-no-association']))") >/dev/null; echo "  exit=\$?  (2 == refused)"
echo; echo "\\\$ .venv/bin/cairn intersect ... cern trio"; .venv/bin/cairn intersect 'fixtures/*.json' --claims \$(.venv/bin/python -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-cern-astro-stability','claim-cern-wd-ns-bound','claim-cern-moon-strangelet']))") >/dev/null; echo "  exit=\$?  (2 == refused)"
T1=\$(date +%s); hr
echo ">>> WALL CLOCK (git clone -> passing demo + all cairn commands): \$((T1-T0))s"
echo ">>> (+ base-image git install overhead: \$((APT1-APT0))s)"; hr; echo "DONE."
INNER

docker run --rm \
  -v "$WORK/cairn.bundle":/seed/cairn.bundle:ro \
  -v "$WORK/run.sh":/run.sh:ro \
  python:3.12-slim bash /run.sh
