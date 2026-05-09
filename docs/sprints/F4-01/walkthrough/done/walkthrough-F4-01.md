# Walkthrough - Sprint F4-01 (Smart Import Architecture)

## What was built
This sprint establishes the architecture and staging schema for our new Smart Import feature. Our problem was that budget spreadsheets (PQs, TCPO, BASES) arrive in highly variable formats, breaking rigid parsers.

We implemented an architecture spike to handle this:
1. **`SmartImportJob` Table:** A new persistent staging area in the database using JSONB columns to hold `mapping_metadata` (how we deduced the columns) and `payload_staging` (the extracted rows, both valid and invalid).
2. **Strict Contracts (Pydantic):** A set of Pydantic models in `smart_import.py` validate the staging payload, so the frontend and backend agree on the schema of the JSON fields.
3. **Pipeline Service Spike:** `smart_import_service.py` provides the scaffold for the new flow:
   - Takes a file, extracts unstructured data (Docling concept).
   - Maps and normalizes the data to our `PqItem` expected fields.
   - Pushes it all to the staging database table with a `REVIEW_REQUIRED` or `COMPLETED` status.
   - Allows a final human validation step before a transactional DB commit.

## How to Test the Spike
- The spike does not expose any new HTTP endpoints yet. However, the service logic is fully functional in memory.
- You can manually test the pipeline logic via a Python REPL or wait for the next sprint (F4-02) where FastAPI routes will be wired to `smart_import_service.create_import_job`.
- Run Alembic migrations via `alembic upgrade head` to deploy the `smart_import_jobs` table to your local DB.
