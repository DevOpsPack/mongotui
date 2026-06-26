# Monitoring

## Server Overview

The **Overview** tab shows:

| Metric | Description |
|--------|-------------|
| Host | Server hostname |
| Version | MongoDB version |
| Uptime | Time since server start |
| Connections | Current / available |
| Memory | Resident and virtual (MB) |
| Storage Engine | WiredTiger, etc. |
| Operations | Insert, query, update, delete counts |
| Replica Set | Name and member count (or Standalone) |
| Databases | Total count |

## Live Performance Graphs

Click **Performance** in the sidebar to see real-time graphs updating every 2 seconds:

- **Connections** — active client connections over time
- **Operations / 2s** — rate of insert + query + update + delete
- **Memory (MB)** — resident memory usage trend

Keeps 60 data points (2 minutes of history).

## Replica Set Status

If connected to a replica set, the Overview shows member count. The replica set info includes:

- Set name
- Member states (PRIMARY, SECONDARY, ARBITER)
- Health status
- Uptime per member
- Replication lag
