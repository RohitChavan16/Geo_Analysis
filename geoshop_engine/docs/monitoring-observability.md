# Monitoring And Observability

## Implemented Signals

| Signal | Implementation |
| --- | --- |
| API health | `GET /api/health` |
| Database health | `GET /api/health/database` |
| Sync status | `GET /api/sync/status` |
| Live progress | `GET /api/sync/progress` |
| Sync history | MongoDB `sync_logs` collection |
| Console logs | `print()` calls in fetchers, pipeline, database setup |

## Not Implemented

- Prometheus metrics.
- Grafana dashboards.
- Structured JSON logging.
- Distributed tracing.
- Error aggregation.
- Alerting.
- Synthetic checks.

## Recommended Metrics

- Source fetch duration by source.
- Source fetch record count by source.
- Source fetch failure count by source.
- Match group count.
- New, updated, closed counts per run.
- Sync duration and status.
- API request count, latency, and error rate.
- MongoDB query latency.
- Queue depth if a worker queue is added.

## Recommended Logs

Use structured JSON logs with:

- `run_id`
- `stage`
- `source`
- `duration_ms`
- `record_count`
- `error_type`
- `error_message`

## Alerting Rules

- Sync failed.
- No successful sync in expected interval.
- All sources return zero records.
- MongoDB health check fails.
- API 5xx rate exceeds threshold.
- Debug endpoint called in production.

