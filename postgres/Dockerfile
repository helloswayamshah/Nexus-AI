# syntax=docker/dockerfile:1.7
# Postgres 18 + pgvector built from source.
# pgvector doesn't ship a pre-built image for pg18 yet, so we compile it.
FROM postgres:18-alpine AS pgvector-builder

RUN apk add --no-cache git build-base clang19 llvm19-dev

# Pin to a released tag — bump when pgvector releases pg18 support officially
ARG PGVECTOR_VERSION=v0.8.0
RUN git clone --depth 1 --branch ${PGVECTOR_VERSION} https://github.com/pgvector/pgvector.git /pgvector

WORKDIR /pgvector
RUN make && make install


FROM postgres:18-alpine

# Copy the compiled pgvector extension files from builder
COPY --from=pgvector-builder /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/
COPY --from=pgvector-builder /usr/share/postgresql/extension/vector* /usr/share/postgresql/extension/

LABEL org.opencontainers.image.description="Postgres 18 + pgvector"
