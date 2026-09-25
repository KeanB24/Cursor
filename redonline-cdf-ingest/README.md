# Red Online → Cognite Action Item Management Ingest

Python scaffold that pulls EHS actions, tasks, and categories from **Red Online**
(REST + token auth), stages them in **Cognite RAW**, then upserts instances into
the existing **Action Item Management** data model views.

Runs as a **Cognite Function** (`handler.py`) or a **VM/CLI script**
(`scripts/run_local.py`) on a schedule.

## Architecture

1. Authenticate to Red Online (bearer token or OAuth client credentials).
2. Extract entities via a config-driven REST client (`config/endpoints.yaml`).
3. Upsert into Cognite RAW staging tables (`redonline_staging`).
4. Map RAW columns → DM view properties (`config/field_maps.yaml`).
5. Upsert nodes with `client.data_modeling.instances.apply`.
6. Persist watermarks in RAW `ingestion_state` for incremental pulls.

## Quick start (local / VM)

```bash
cd redonline-cdf-ingest
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

copy .env.example .env
# Edit .env with CDF + Red Online credentials when on the office network
```

### Offline dry-run (no live APIs)

```bash
# Uses fixtures/ JSON instead of calling Red Online
set REDONLINE_MOCK=1
python scripts/run_local.py --mock --dry-run
```

`--dry-run` skips Cognite writes and prints what would be staged/loaded.

### Live run

```bash
python scripts/run_local.py
```

Schedule with Windows Task Scheduler or cron using the same command.

## Cognite Function

Deploy the package as a Cognite Function. Entry point:

```python
# handler.py
def handle(data, client):
    ...
```

- Attach Cognite credentials via Function secrets / the injected `client`.
- Set Red Online secrets (`REDONLINE_TOKEN`, `REDONLINE_BASE_URL`, …) as Function secrets.
- Schedule with a CDF Function schedule (suggested cron in `config/settings.yaml`: every 6 hours).

## Configuration to fill in on the office laptop

| File | What to replace |
|------|-----------------|
| `.env` | Real CDF project/cluster/OIDC and Red Online token |
| `config/endpoints.yaml` | Real paths, pagination, response item paths |
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
```

## Tests

```bash
pytest
```
