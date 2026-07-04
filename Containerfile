# The decoupled scoring engine as one plain container.
#   build:  docker build -t cairn -f Containerfile .
#   run:    docker run --rm cairn                 # the HSM-trio head-to-head
#   verify: (tests run at build time; build fails if they don't pass)
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml requirements.txt ./
COPY cairn ./cairn
COPY schemas ./schemas
COPY fixtures ./fixtures
COPY demo ./demo
COPY tests ./tests

RUN pip install --no-cache-dir -e . && pip install --no-cache-dir pytest

# self-verifying image: mint fixtures + prove the spans resolve + run the suite at build time
RUN python fixtures/build_fixtures.py >/dev/null \
 && python -m cairn ground 'fixtures/*.json' >/dev/null \
 && python -m pytest -q

CMD ["python", "demo/hsm_trio.py"]
