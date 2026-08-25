# Headless altastata-services (S3 + gRPC + Web Console) — MCP OFF
#
# Build context: repo root `/Users/sergevilvovsky/eclipse-workspace/mcloud`
#
# Inputs (current local build artefacts):
# - mycloud/altastata-services/build/libs/altastata-services-2026.08.25-uber.jar
# - mycloud/altastata-services/build/libs/lib/
# - altastata-python-package/altastata/lib/altastata-console-static/

FROM eclipse-temurin:17-jdk-jammy

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8 -Duser.language=en -Duser.country=US"

RUN useradd -r -u 1001 -g root appuser

WORKDIR /app

COPY mycloud/altastata-services/build/libs/altastata-services-2026.08.25-uber.jar /app/app.jar
COPY mycloud/altastata-services/build/libs/lib /app/lib
COPY altastata-python-package/altastata/lib/altastata-console-static /app/altastata-console-static

RUN chown -R appuser:root /app && \
    chmod -R 755 /app && \
    chmod 644 /app/app.jar /app/lib/*.jar || true

USER appuser

EXPOSE 9876 9877

# Service gates: keep MCP OFF; enable S3 + gRPC + Web Console.
ENV ALTASTATA_GRPC_BIND_ADDRESS=0.0.0.0
ENV ALTASTATA_SERVICES_S3GATEWAY_ENABLED=true
ENV ALTASTATA_SERVICES_GRPC_ENABLED=true
ENV ALTASTATA_SERVICES_PY4J_ENABLED=false
ENV ALTASTATA_SERVICES_MCP_ENABLED=false
ENV ALTASTATA_WEB_UI_DIR=/app/altastata-console-static

ENTRYPOINT ["java","-jar","/app/app.jar"]

