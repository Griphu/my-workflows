FROM mediforce-golden-image

# Kaggle CLI / Python client for the fetch_competitions and submit_kaggle steps.
RUN pip install --no-cache-dir --break-system-packages "kaggle==1.6.17"

# Build context is this file's directory (kaggle-competition-coordination/),
# so scripts/ resolves to kaggle-competition-coordination/scripts/.
COPY scripts/ /opt/kaggle/scripts/

WORKDIR /workspace
