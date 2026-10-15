# Week 6 — Kafka Event Streaming Stack

Two decoupled microservices communicating over Kafka, fully containerized.

- **blog_app** (`:8000`) — FastAPI blog API. On post/comment creation it **publishes**
  an event to Kafka (fire-and-forget). Backed by Postgres.
- **activity-service** (`:9000`) — ITaaP-template microservice. **Consumes** blog events
  in a background task and exposes them at `GET /activity-service/activity`.
  Also exports request **traces to Elasticsearch** (viewable in Kibana).
- Infra: **Kafka** (+ Kafka-UI), **Postgres**, **Elasticsearch** (+ Kibana).

## Run the whole thing (one command)

Requires Docker Desktop.

```bash
docker compose up --build
```

First run builds both app images and pulls the infra images — give it a few minutes.
Kafka and Elasticsearch have healthchecks; the apps wait for them to be ready.

## Verify end to end (curl)

```bash
# register + login
curl -s -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"password123"}'

TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=demo&password=password123" | jq -r .access_token)

# create a post -> publishes a Kafka event
curl -i -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"hello","body":"first event"}'

# the consumer picked it up
curl -s http://localhost:9000/activity-service/activity | jq
```

## URLs

| URL | What |
|---|---|
| http://localhost:8000 | blog_app API |
| http://localhost:9000/activity-service/activity | recent consumed events |
| http://localhost:8080 | Kafka-UI (topics, messages, consumer groups) |
| http://localhost:5601 | Kibana (request traces — data view `activity-service*`) |

## Notes

- `activity-service` installs the private `itaap-python-utils` from the bundled wheel
  in `activity-service/wheels/` (no Azure feed needed).
- Auth on `activity-service` is bypassed locally via `APP_ENV=local` + `AUTH_DISABLED=true`
  (set in `docker-compose.yml`) — never active outside a local environment.
- All service config is injected by `docker-compose.yml`; no `.env` files are required.
