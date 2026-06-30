FROM mediforce-golden-image

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages \
    "kaggle==1.6.17" \
    "requests==2.32.3"

COPY scripts/ /opt/kaggle-coordinator/scripts/

WORKDIR /workspace
