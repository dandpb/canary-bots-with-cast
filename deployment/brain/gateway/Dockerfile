FROM python:3.12-slim
COPY deployment/brain/gateway/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r /app/requirements.lock
WORKDIR /app
COPY deployment/brain/src/canary_brain/gateway_policy.py /app/gateway_policy.py
ENV PYTHONPATH=/app LITELLM_LOCAL_MODEL_COST_MAP=true CANARY_GATEWAY_CONFIG=/app/gateway.yaml
ENTRYPOINT ["litellm", "--config", "/app/gateway.yaml", "--host", "0.0.0.0", "--port", "4000"]
