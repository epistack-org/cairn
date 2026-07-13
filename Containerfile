# The decoupled scoring engine as one plain container.
#   build:  docker build -t cairn -f Containerfile .
#   run:    docker run --rm cairn                                  # the HSM-trio head-to-head
#          docker run --rm cairn python demo/worked_examples.py   # all 3 worked examples
#   verify: (tests run at build time; build fails if they don't pass)
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml requirements.txt ./
COPY cairn ./cairn
COPY schemas ./schemas
COPY fixtures ./fixtures
COPY demo ./demo
COPY tests ./tests
COPY assessment ./assessment

RUN pip install --no-cache-dir -e . && pip install --no-cache-dir pytest

# self-verifying image: mint the fixtures for all 3 worked examples + prove every span
# resolves + recompute the measured n_eff from the pinned assessment run + prove EACH
# case refuses (exit 2) + run the suite, all at build time.
#
# `build_fixtures.py` additionally verifies each case's DECLARED structure (fixtures/
# CASES.json) against what the provenance detector actually finds, and fails the build if
# a laundered set stops refusing or its shared upstream is not the one named.
RUN python fixtures/build_fixtures.py >/dev/null \
 && python -m cairn ground 'fixtures/*.json' >/dev/null \
 && python -m cairn assess 'assessment/runs/heterogeneous.json' 'assessment/runs/homogeneous-control.json' 'assessment/runs/clean-diverse.json' 'assessment/runs/glm-diverse.json' --battery assessment/probes.json >/dev/null \
 && ( python -m cairn frechet fixtures/claim-geographic-clustering.json fixtures/claim-environmental-sampling.json fixtures/claim-live-mammal-sales.json fixtures/src-worobey-2022.json >/dev/null ; test $? -eq 2 ) \
 && ( python -m cairn intersect 'fixtures/*.json' --claims $(python -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-eggs-rong-no-association','claim-eggs-godos-no-association','claim-eggs-drouin-no-association']))") >/dev/null ; test $? -eq 2 ) \
 && ( python -m cairn intersect 'fixtures/*.json' --claims $(python -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-cern-astro-stability','claim-cern-wd-ns-bound','claim-cern-moon-strangelet']))") >/dev/null ; test $? -eq 2 ) \
 && ( python -m cairn headtohead 'fixtures/*.json' >/dev/null ; test $? -eq 2 ) \
 && python demo/worked_examples.py >/dev/null \
 && python -m pytest -q

# the deep view (COVID: naive + careful baseline vs cairn, the four deltas) stays the
# default. The wide view — all three worked examples — is one flag away:
#   docker run --rm cairn python demo/worked_examples.py
CMD ["python", "demo/hsm_trio.py"]
