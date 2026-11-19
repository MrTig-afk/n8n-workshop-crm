# Workshop CRM API

A small FastAPI CRUD API backed by Neon PostgreSQL for the n8n workshop.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API and database connectivity |
| POST | `/leads` | Create a lead |
| GET | `/leads` | List all leads |
| GET | `/leads/{id}` | Retrieve one lead |
| PATCH | `/leads/{id}` | Update selected lead fields |
| DELETE | `/leads/{id}` | Delete a lead |

Interactive API documentation is available at `/docs`.

## Environment variable

Set `DATABASE_URL` to the Neon pooled PostgreSQL connection string.

## Render start command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
