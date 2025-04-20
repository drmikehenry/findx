FROM ubuntu:14.04

RUN apt update \
  && apt install -y \
      binutils \
      curl \
  && rm -rf /var/lib/apt/lists/*

ARG FINDX_UV_VERSION="0.7.2"
ARG FINDX_UV_PYTHON_VERSION="3.13"
ARG FINDX_UV_PACKAGE="uv-x86_64-unknown-linux-musl.tar.gz"
ARG FINDX_UV_DOWNLOAD_BASE="https://github.com/astral-sh/uv/releases/download"
ARG FINDX_UV_URL="$FINDX_UV_DOWNLOAD_BASE/$FINDX_UV_VERSION/$FINDX_UV_PACKAGE"

RUN curl -L "$FINDX_UV_URL" -o "/tmp/$FINDX_UV_PACKAGE" \
  && tar -C /tmp -xf "/tmp/$FINDX_UV_PACKAGE" \
  && cp /tmp/uv-*/uv* /usr/local/bin \
  && rm -rf /tmp/uv*

RUN uv python install "$FINDX_UV_PYTHON_VERSION"

# Copy in project dependency specifications that don't change often; this
# speeds up incremental rebuilding of the container.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-package findx

COPY README.rst \
  maintainer.rst \
  noxfile.py \
  findx-wrapper.py \
  ffx-wrapper.py \
  ffg-wrapper.py \
  src \
  ./

RUN uv run nox -s build \
  && cp dist/x86_64-linux/* /usr/local/bin

ENTRYPOINT ["findx", "--version"]
