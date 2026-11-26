# DBA-Pulse API

REST API built with FastAPI. It sits in front of `src/database.py` (SQLite).
All SQL stays in `database.py`; `src/api.py` only handles HTTP.

## Run the server

```
python -m uvicorn src.api:app --reload
```

- Base URL: `http://127.0.0.1:8000`
- Interactive docs (Swagger): `http://127.0.0.1:8000/docs`

## Endpoints

| Method | Endpoint | Purpose | Success | Errors |
|---|---|---|---|---|
| GET | `/` | Health check | 200 | - |
| GET | `/runs?limit=20` | List latest runs (limit 1-200) | 200 | 400 |
| GET | `/runs/{id}` | Get one run | 200 | 404 |
| GET | `/runs/{id}/findings` | Findings of one run | 200 | 404 |
| POST | `/runs` | Create a run with findings | 201 | 422 |
| PUT | `/runs/{id}/status` | Update overall status | 200 | 404, 422 |
| DELETE | `/runs/{id}` | Delete a run and its findings | 200 | 404 |
| GET | `/report` | Latest HTML report | 200 | 404 |

## Examples

**POST /runs**

Request body:

```json
{
  "overall_status": "WARNING",
  "findings": [
    {"area": "Tablespace", "severity": "MEDIUM", "message": "USERS_DATA is 91.0% full."}
  ]
}
```

Response (201):

```json
{"message": "Run created", "run_id": 5}
```

**PUT /runs/5/status**

Request body: `{"overall_status": "OK"}`

Response (200):

```json
{"message": "Status updated", "run_id": 5, "overall_status": "OK"}
```

**GET /runs/999**

Response (404): `{"detail": "Run 999 not found"}`

## Validation rules

- `overall_status`: one of `OK`, `WARNING`, `CRITICAL`
- `severity`: one of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- `message`: required, not empty
- `limit`: between 1 and 200

## Error codes

| Code | Meaning |
|---|---|
| 400 | Bad query value (for example `limit=500`) |
| 404 | Run or report not found |
| 422 | Invalid request body (wrong status or severity, missing field) |

## Testing

Automated tests are in `tests/test_api.py` and use a temporary database,
so the real `dba_pulse.db` is never changed.

```
python -m unittest discover -s tests -p "test_*.py" -v
```

