# Red Online → Cognite Action Item Management Ingest

Python scaffold that pulls HSE Compliance data from **Red Online**
(REST + `X-ROL-API-KEY` auth), stages it in **Cognite RAW**, then upserts
instances into the existing **Action Item Management** data model views.

Runs as a **Cognite Function** (`handler.py`) or a **VM/CLI script**
(`scripts/run_local.py`) on a schedule.

## Architecture

1. Authenticate to HSE / Red Online with header `X-ROL-API-KEY`.
2. Extract entities via a config-driven REST client (`config/endpoints.yaml`).
3. Upsert into Cognite RAW staging tables (`redonline_staging`).
4. Map RAW columns → DM view properties (`config/field_maps.yaml`).
5. Upsert nodes with `client.data_modeling.instances.apply`.
6. Persist watermarks in RAW `ingestion_state` for incremental pulls.

## HSE Compliance API (ct-test)

Configured from `hse_compliance_api_endpoints.md`:

| Endpoint | Path |
|----------|------|
| Sites | `GET /v2/secure-clients/legapi-general/sites` |
| Users by site | `GET /v2/secure-clients/legapi-general/users/sites/{site_id}` |
| Mapping references | `GET /v2/secure-clients/tasks/configs/references?user_id={user_id}` |
| Tasks by user | `GET /v2/secure-clients/tasks?user_id={user_id}` |

- **Auth**: header `X-ROL-API-KEY` (set `REDONLINE_API_KEY` in `.env`, or the fallback in `config/endpoints.yaml`)
- **Base URL**: `https://apigw.ct-test.hse-compliance.net`
- **Defaults**: `site_id=112087`, `user_id=584646` (override with `REDONLINE_SITE_ID` / `REDONLINE_USER_ID`)

## Execution steps

### 1. Set up env

```powershell
cd redonline-cdf-ingest
copy .env.example .env
```

You must be inside the `redonline-cdf-ingest` folder (where `requirements.txt` lives).

Edit `.env` and set real Cognite OIDC values (`CDF_CLIENT_ID`, `CDF_CLIENT_SECRET`, `CDF_TENANT_ID`).
The HSE API key and base URL are already filled from the ct-test details.

If you skip `.env`, the client can still use `auth.api_key` from `config/endpoints.yaml`.

### 2. Install packages (once, no virtualenv)

Use your normal Python (e.g. Anaconda or system Python). No `.venv` needed.

```powershell
cd redonline-cdf-ingest
python -m pip install -r requirements.txt
python -m pip install -e .
```

If you use Anaconda for notebooks/Jupyter, install with that interpreter so the same packages are available there:

```powershell
C:\Users\neelk\anaconda3\python.exe -m pip install -r requirements.txt
C:\Users\neelk\anaconda3\python.exe -m pip install -e .
```

### 3. Dry-run with fixtures (no network)

```powershell
python scripts/run_local.py --mock --dry-run
```

Confirms extract/map logic without calling HSE or Cognite.

### 4. Discover live ROL response shapes (for RAW table design)

Best way to design Cognite RAW tables: call each ROL API once, save the JSON,
then build columns from the real fields.

```powershell
python scripts/discover_rol_schema.py --insecure
```

`--insecure` disables TLS verify (needed on many corporate laptops that show
`CERTIFICATE_VERIFY_FAILED`). Same effect: `REDONLINE_VERIFY_SSL=0` in `.env`.

This script is **standalone** (stdlib + PyYAML only). It does **not** import
`src/redonline_cdf`.

Optional — only some endpoints:

```powershell
python scripts/discover_rol_schema.py --insecure --endpoints list_sites list_tasks_by_user
```

Or use the simple notebook (no package imports):

```text
notebooks/call_rol_apis.ipynb
```

This writes under `samples/rol/` (gitignored):

| File | Purpose |
|------|---------|
| `<endpoint>_raw.json` | Full API response |
| `<endpoint>_items.json` | Extracted row list (best effort) |
| `schema_summary.md` | Field catalog + suggested `items_path` / id field |
| `schema_summary.json` | Same summary as JSON |

Then:

1. Open `samples/rol/*_raw.json` and confirm the shape.
2. Set `items_path` in `config/endpoints.yaml` if responses are wrapped (e.g. `data` / `items`).
3. Set `id_field` in `config/settings.yaml` from the suggested key.
4. Map properties in `config/field_maps.yaml` using `schema_summary.md`.

### 5. Live HSE pull only (no Cognite write)

```powershell
python scripts/run_local.py --dry-run
```

Calls the real HSE APIs with `X-ROL-API-KEY` and prints what would be staged/loaded.

### 6. Full ingest into Cognite

```powershell
python scripts/run_local.py
```

Pulls HSE → stages RAW → upserts into the Action Item Management views.

### 7. Optional: single entity

```powershell
python scripts/run_local.py --entities tasks
```

Also valid: `sites`, `users`, `references`.

### 8. Cognite Function (later)

Deploy with `handler.py` as the entrypoint:

```python
def handle(data, client):
    ...
```

- Put `REDONLINE_API_KEY`, `REDONLINE_BASE_URL`, and CDF secrets in Function secrets
  (or use the injected `client` for Cognite).
- Schedule via CDF Function cron (suggested in `config/settings.yaml`: every 6 hours).

On a VM, schedule the same CLI with Windows Task Scheduler or cron.

## Configuration checklist (office laptop)

| File | What to replace |
|------|-----------------|
| `.env` | CDF OIDC credentials; confirm `REDONLINE_API_KEY` / site / user IDs |
| `config/endpoints.yaml` | Adjust `items_path` after inspecting live JSON responses |
| `config/settings.yaml` | Real DM `instance_space`, view `external_id` / `version` |
| `config/field_maps.yaml` | Real view property names matching the live model |

## Project layout

```
config/           settings, endpoints, field maps
fixtures/         sample JSON for mock mode
src/redonline_cdf/
  auth/           Cognite + Red Online auth
  redonline/      config-driven REST client
  cognite/        RAW staging + DM loader
  pipeline/       orchestration + watermark state
  models/         Pydantic DTOs
handler.py        Cognite Function entry
scripts/run_local.py
tests/
notebooks/        Cognite connection sample
```

## Package layout note

Code lives under `src/redonline_cdf/` (standard Python `src` layout). That is why
imports look like `from redonline_cdf...` — the folder is `src/redonline_cdf`, not
a top-level `redonline_cdf/`. Discovery/notebooks do **not** need that package.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `No such file: requirements.txt` | `cd` into `redonline-cdf-ingest` first |
| `Set REDONLINE_API_KEY...` | Copy `.env.example` → `.env`, or keep `auth.api_key` in `endpoints.yaml` |
| `REDONLINE_BASE_URL is required` | Set in `.env` or `base_url` in `endpoints.yaml` |
| `CERTIFICATE_VERIFY_FAILED` | `python scripts/discover_rol_schema.py --insecure` or `REDONLINE_VERIFY_SSL=0` |
| Hard to debug ingest pipeline | Prefer `notebooks/call_rol_apis.ipynb` or `discover_rol_schema.py` first |

## Tests

```powershell
pytest
```
