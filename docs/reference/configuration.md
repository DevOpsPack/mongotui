# Configuration

## Command Line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--uri` | `-u` | MongoDB connection URI (skips connect screen) |

## Connection URI Format

```
mongodb://[username:password@]host[:port][/database][?options]
```

### Examples

```bash
# Local without auth
mongotui -u "mongodb://localhost:27017"

# Local with auth
mongotui -u "mongodb://admin:admin@localhost:27017/?authSource=admin"

# Replica set
mongotui -u "mongodb://host1:27017,host2:27017,host3:27017/?replicaSet=rs0&authSource=admin"

# Atlas
mongotui -u "mongodb+srv://user:pass@cluster.mongodb.net/?authSource=admin"
```

### Important options

| Option | Description |
|--------|-------------|
| `authSource=admin` | Database to authenticate against (usually `admin`) |
| `replicaSet=name` | Replica set name |
| `directConnection=true` | Connect to a single node directly |
| `tls=true` | Enable TLS/SSL |

## Docker Compose

The project includes a `docker-compose.yml` for local testing:

```bash
docker compose up -d
mongotui -u "mongodb://admin:admin@localhost:27017/?authSource=admin"
```
