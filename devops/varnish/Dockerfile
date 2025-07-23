# syntax=docker/dockerfile:1
FROM varnish:7.6

LABEL maintainer="Darren Lund <darren.lund@gauntletai.com>" \
      org.label-schema.name="knowledge-curator-varnish" \
      org.label-schema.description="Knowledge Curator Varnish image." \
      org.label-schema.vendor="Darren Lund"

COPY etc/varnish.vcl /etc/varnish/default.vcl
