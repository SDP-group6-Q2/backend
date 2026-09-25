#!/bin/sh
# Brings the database up to date before the API starts. Every step is idempotent.
set -e

echo "init: migrating the database"
alembic upgrade head

echo "init: creating the first superuser"
python -m app.initial_data

# Fleet dataset (machines, telemetry, quotes, ...). Skipped when there is no dataset file mounted.
DATASET_FILE="${DATASET_PATH:-/app/data/AROL_Q2_synthetic_fleet_dataset.xlsx}"
if [ "${SEED_DATASET:-true}" = "true" ]; then
    if [ -f "$DATASET_FILE" ]; then
        echo "init: loading the fleet dataset from $DATASET_FILE"
        python -m app.seed_dataset
    else
        echo "init: no dataset at $DATASET_FILE, skipping the dataset load"
    fi
fi

# Link machines to their manual PDFs in the Supabase bucket. Needs the network and credentials, so a
# failure here is reported but does not stop the API.
if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "init: linking machines to their manuals"
    python -m app.sync_manuals || echo "init: WARNING: manual linking failed; run 'python -m app.sync_manuals' later"
fi

exec "$@"
