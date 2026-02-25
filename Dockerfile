# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker/54763270#54763270

FROM python:3.14


# --------------------------------------
# ------------- Set labels -------------

# See https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL name="pre-commit-matlab-lint"
LABEL version="1.0.7"
LABEL vendor="ty.cumby"
LABEL org.opencontainers.image.title="pre-commit-matlab-lint"
LABEL org.opencontainers.image.version="1.0.7"
LABEL org.opencontainers.image.url="https://github.com/ty.cumby/pre-commit-matlab-lint"
LABEL org.opencontainers.image.documentation="https://github.com/ty.cumby/pre-commit-matlab-lint"


# --------------------------------------
# ---------- Copy and install ----------

# Configure env variables for build/install
# ENV no longer adds a layer in new Docker versions,
# so we don't need to chain these in a single line
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=120
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY uv.lock pyproject.toml /code/

# Install with uv
RUN uv sync --frozen --no-dev

# Copy everything (code) to our workdir
COPY . /code

# Install the project
RUN uv pip install .


# --------------------------------------
# --------------- Run! -----------------

# Now do something!
CMD precommitmatlablint --help

# Perhaps run a command:
# CMD precommitmatlablint --my --options --etc
# or expose a port:
# EXPOSE 443/tcp
