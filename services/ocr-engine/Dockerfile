FROM registry:5000/auth:prod-latest AS auth_runtime
FROM registry:5000/ai-engine:prod-latest

WORKDIR /app

# Reuse the already-built runtime from ai-engine to avoid internet-dependent pip installs
# during CI builds on the local runner.
COPY --from=auth_runtime /usr/local/lib/python3.11/site-packages/prometheus_client /opt/conda/lib/python3.11/site-packages/prometheus_client
COPY --from=auth_runtime /usr/local/lib/python3.11/site-packages/prometheus_client-0.20.0.dist-info /opt/conda/lib/python3.11/site-packages/prometheus_client-0.20.0.dist-info

COPY app /app/app

EXPOSE 8091

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8091"]
