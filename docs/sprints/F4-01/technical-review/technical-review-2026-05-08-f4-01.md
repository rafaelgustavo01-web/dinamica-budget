# Technical Review - Sprint F4-01 (Smart Import Architecture)

## Context
The goal of this sprint is to lay the foundation for a "Smart Import" pipeline. The core principle is "Tolerant Input. Strict Core. Protected Database." This means accepting messy files, leveraging Docling/heuristics to parse them, mapping them to strict Pydantic schemas, and exposing a human-in-the-loop staging area before executing any database transaction.

## Architectural Decisions
1. **Separation of Concerns:** 
   - Created `SmartImportJob` table to represent the lifecycle and staging of the import process. This isolates the experimental/flexible parsing phase from the transactional finalization.
2. **Staging Schema:**
   - Instead of breaking `PqImportacao` or injecting unstructured data into existing normalized tables, we use `mapping_metadata` (JSONB) and `payload_staging` (JSONB) in the `SmartImportJob`.
   - Strict `Pydantic` schemas (`SmartImportPayload`, `StagingRow`, etc.) represent the JSONB contracts, ensuring data integrity while inside the staging payload.
3. **Database Migration (Alembic):**
   - Safe migration (`027_smart_import_job_table.py`) added to create `smart_import_jobs` in the `operacional` schema along with its ENUMs. No existing schemas (`pq_importacoes` or `pq_itens`) are mutated, guaranteeing zero regression risk for the current system.
4. **Service Spike:**
   - Delivered `app/backend/services/smart_import_service.py` outlining the exact workflow: `Extractor -> Normalizer -> Staging -> Validation -> Transactional Commit`. Currently mocked for the Extractor (Docling placeholder) but fully typing-ready.

## Risks & Mitigation
- **JSONB Overhead:** If Excel files get too large (e.g., >50MB), storing them inside JSONB could consume significant database memory. This is mitigated by keeping only valid/invalid rows in the StagingPayload after normalization, not raw byte data.
- **Rollback:** Any commit from Staging to Production runs inside an async session block. It fails safely without partial writes.

## Checked
- [x] Models and Schemas properly defined with Pydantic and SQLAlchemy.
- [x] Migration script 027 generated correctly matching `down_revision = '026'`.
- [x] Spike module created, isolated, and typed.
- [x] Existing pipelines and import routes remain untouched.
