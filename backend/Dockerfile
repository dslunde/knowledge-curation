# syntax=docker/dockerfile:1
ARG PLONE_VERSION=6.1.2
FROM plone/server-builder:${PLONE_VERSION} AS builder

WORKDIR /app


# Add local code
COPY scripts/ scripts/
COPY . src

# Install local requirements and pre-compile mo files
RUN <<EOT
    set -e
    bin/pip install mxdev uv
    sed -i 's/-e .\[test\]/./g' src/mx.ini
    cd /app/src
    # remove potentially existing virtualenv from local build
    rm -rf .venv
    ../bin/mxdev -c mx.ini
    ../bin/uv pip install -r requirements-mxdev.txt
    ../bin/python /compile_mo.py
EOT

FROM plone/server-prod-config:${PLONE_VERSION}

LABEL maintainer="Darren Lund <darren.lund@gauntletai.com>" \
      org.label-schema.name="knowledge-curator-backend" \
      org.label-schema.description="Knowledge Curator backend image." \
      org.label-schema.vendor="Darren Lund"

# Copy /app from builder
COPY --from=builder /app /app

# Copy Extensions directory for external methods
COPY --from=builder /app/src/instance/Extensions /app/Extensions
RUN <<EOT
    set -e
    ln -s /data /app/var
EOT
