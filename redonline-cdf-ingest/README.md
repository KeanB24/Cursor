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

Edit `.env` and set real Cognite OIDC values (`CDF_CLIENT_ID`, `CDF_CLIENT_SECRET`, `CDF_TENANT_ID`).
The HSE API key and base URL are already filled from the ct-test details.

### 2. Install (once)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 3. Dry-run with fixtures (no network)

```powershell
python scripts/run_local.py --mock --dry-run
```

Confirms extract/map logic without calling HSE or Cognite.

### 4. Live HSE pull only (no Cognite write)

```powershell
python scripts/run_local.py --dry-run
```

Calls the real HSE APIs with `X-ROL-API-KEY`. If responses are wrapped
(e.g. `{"data":[...]}`) instead of a bare list, set `items_path` in
`config/endpoints.yaml` accordingly.

### 5. Full ingest into Cognite

```powershell
python scripts/run_local.py
```

Pulls HSE → stages RAW → upserts into the Action Item Management views.

### 6. Optional: single entity

```powershell
python scripts/run_local.py --entities tasks
```

Also valid: `sites`, `users`, `references`.

### 7. Cognite Function (later)

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

## Tests

```powershell
pytest
```
