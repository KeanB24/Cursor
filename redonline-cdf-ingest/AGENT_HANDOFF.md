# Agent handoff — Red Online → Cognite ingest

Compressed context for the next agent. Project root: `redonline-cdf-ingest/`.

## Goal
Ingest HSE / Red Online (ROL) data into Cognite Data Fusion RAW DB **`ROL-COR`**, then later into Action Item Management data model views.

## What was built
- Python package under `src/redonline_cdf/` (src layout).
- Config-driven ROL client: `config/endpoints.yaml` + header auth `X-ROL-API-KEY`.
- Standalone discovery: `scripts/discover_rol_schema.py` (stdlib+PyYAML, `--insecure` for corp SSL).
- Simple notebook: `notebooks/call_rol_apis.ipynb` (hardcoded ROL calls).
- Cognite notebook: `notebooks/connect_cognite.ipynb`.
- Cascaded ingest pipeline: **sites → users per site → tasks per user → references once**.
- Flatteners → Uppercase RAW tables in `ROL-COR`.
- First wave: **RAW only** (`load_to_data_model: false`).

## Credentials / endpoints (also in `.env` / config)
| Item | Value |
|------|--------|
| ROL base | `https://apigw.ct-test.hse-compliance.net` |
| ROL auth | Header `X-ROL-API-KEY` = `9f5ef52b-b98d-4cdb-9672-e423cc9051d5` |
| CDF project | `celanese` |
| CDF cluster | `az-eastus-1` |
| CDF client id | `cb909a16-1087-4e06-9d11-8dfbd6ae1a5c` |
| CDF tenant | `7a3c88ff-a5f6-449d-ac6d-e8e3aa508e37` |
| CDF secret | in `.env` — Azure may reject if expired (`AADSTS7000215`); rotate if needed |
| Corp SSL | `REDONLINE_VERIFY_SSL=0` in `.env`, or `--insecure` on **both** `discover_rol_schema.py` and `run_local.py` |

## ROL APIs
1. `GET /v2/secure-clients/legapi-general/sites` → items at `sites`
2. `GET /v2/secure-clients/legapi-general/users/sites/{site_id}` → `users`
3. `GET /v2/secure-clients/tasks?user_id={user_id}` → `data`
4. `GET /v2/secure-clients/tasks/configs/references?user_id={user_id}` → split `data.*` lookups

Sample payloads: `samples/rol/` (committed). Schema notes: `samples/rol/schema_summary.md`.

## RAW DB `ROL-COR` tables (Uppercase)
| Table | Source |
|-------|--------|
| `Sites` | list_sites |
| `Users`, `User_profiles` | users per site (cascaded) |
| `Tasks`, `Task_instances`, `Task_occurrences` | tasks per user (cascaded) |
| `Ref_categories`, `Ref_priorities`, `Ref_states`, `Ref_occurrence_statuses` | mapping references |
| `Ingestion_state` | watermarks |

## Cascaded ingest (current behavior)
Configured in `config/settings.yaml` (`ingest_mode: cascaded`):
1. Fetch all sites → stage `Sites`
2. For each `id_site` → fetch users → stage `Users` / `User_profiles` (deduped)
3. For each unique `id_user` → fetch tasks → stage task tables (deduped)
4. Fetch references once (first user) → stage `Ref_*`

Limits for testing (optional in settings):
```yaml
cascaded:
  max_sites: 2
  max_users_per_site: 5
  max_users_for_tasks: 5
```

## How to run
No venv required. From `redonline-cdf-ingest/`:
```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
copy .env.example .env   # if missing
python scripts/discover_rol_schema.py --insecure
python scripts/run_local.py --mock --dry-run
python scripts/run_local.py --dry-run --insecure   # live ROL, no CDF write
python scripts/run_local.py --insecure             # live ROL + CDF RAW write
```

## Key files
- `config/settings.yaml` — ROL-COR tables, cascaded limits, DM flag
- `config/endpoints.yaml` — paths, auth, items_path
- `config/field_maps.yaml` — DM mapping (unused while RAW-only)
- `src/redonline_cdf/pipeline/ingest.py` — cascaded orchestration
- `src/redonline_cdf/pipeline/flatten.py` — nested → RAW rows
- `scripts/discover_rol_schema.py` — standalone discovery
- `README.md` — execution steps

## Issues solved along the way
- Wrong cwd for pip (`requirements.txt` not found) → must `cd redonline-cdf-ingest`
- Missing API key / base URL → `.env` + config fallbacks
- `CERTIFICATE_VERIFY_FAILED` on dry-run → discovery had `--insecure` but ingest CLI did not; use `run_local.py --insecure` (now synced) / `REDONLINE_VERIFY_SSL=0`
- `samples/rol/` missing after pull → was gitignored; ignore removed
- Cognite secret invalid (`AADSTS7000215`) → may need new Azure client secret
- `KeyError: CDF_CLIENT_ID` / missing Cognite creds → `--dry-run` skips CDF; full run needs `CDF_PROJECT`, `CDF_CLIENT_ID`, `CDF_CLIENT_SECRET`, `CDF_TENANT_ID` in project-root `.env` (copy from `.env.example`)
- Complex imports confused user → discovery/notebook are standalone; package is under `src/`

## Next work for new agent
1. Run live cascaded ingest into `ROL-COR` on office network; verify tables in CDF.
2. If volume is huge, set `cascaded.max_*` limits first, then full run.
3. Align `field_maps.yaml` + enable `load_to_data_model: true` for Action Item Management views.
4. Optionally expand RAW: `Task_instance_owners`, `Task_instance_reviewers`, more `Ref_*`.
5. Schedule via Cognite Function (`handler.py`) or Windows Task Scheduler.

## Do not
- Do not redeploy/create the Action Item Management data model (already exists).
- Do not commit secrets carelessly; `.env` is gitignored (`.env.example` currently mirrors values for portability).
