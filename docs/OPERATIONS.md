# Operations and Security Playbook

## Key Rotation Strategy

- Rotate all long-lived machine keys on a regular schedule (for example every 60-90 days).
- Prefer shorter expiry windows for external integrations.
- Use overlapping rotation:
  1. create new key (`POST /machine-auth/machine-api-keys/` or Django admin)
  2. deploy new key to client
  3. monitor successful traffic
  4. deactivate old key (`POST /machine-auth/machine-api-keys/{id}/deactivate/` or set `is_active=False` in admin)

Management API access: superusers manage all keys; regular users manage only keys where `MachineAPIKey.user` matches their account. See [setup.md](../setup.md#part-iv--api-key-management).

## Incident Response: Key Compromise

1. Deactivate affected `MachineAPIKey` in admin immediately.
2. Trigger replacement key generation.
3. Communicate client cutoff timeline.
4. Review request logs for abuse indicators (Django admin or `GET /machine-auth/request-logs/` with superuser JWT).
5. Rotate related credentials/tokens if downstream systems may be exposed.

Cache note: key updates invalidate cache entries via model/admin hooks.

## Logging Mode Guidance

- `raw`: use only in tightly controlled debug environments.
- `redacted`: recommended baseline for production.
- `metadata_only`: best for high-compliance environments with strict payload minimization.

## Monitoring Recommendations

Track and alert on:

- authentication failures (invalid/expired/inactive key)
- permission-denied responses
- throttle rejections
- sudden request volume spikes per key
- stale keys not used for long periods (`last_used_at`).

## Suggested Metrics

- `machine_auth.auth.success.count`
- `machine_auth.auth.failure.count`
- `machine_auth.permission.denied.count`
- `machine_auth.throttle.denied.count`
- `machine_auth.request.duration.ms` (timer/histogram)
