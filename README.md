# MongoTUI

<p align="center">
  <img src="assets/logo.png" alt="MongoTUI" width="200">
</p>

[![PyPI](https://img.shields.io/pypi/v/mongotui)](https://pypi.org/project/mongotui/)
[![Python](https://img.shields.io/pypi/pyversions/mongotui)](https://pypi.org/project/mongotui/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![GitHub release](https://img.shields.io/github/v/release/DevOpsPack/mongotui)](https://github.com/DevOpsPack/mongotui/releases)
[![Downloads](https://img.shields.io/pypi/dm/mongotui)](https://pypi.org/project/mongotui/)

A modern terminal user interface for MongoDB administration — like Compass, but for your terminal.

Built with Python, Textual, and PyMongo. Fast, secure, no web UI needed.

## Features

**Database Management**
- Browse databases, collections, and documents
- Create and drop databases
- View collection stats (document count, size)
- Query documents with JSON filters
- Run aggregation pipelines

**User & Role Administration**
- Create and delete users
- Reset passwords
- Grant and revoke roles (built-in role picker)
- Browse all users and their permissions

**Index Management**
- View indexes with size and key info
- Create and drop indexes
- Create search indexes (text & vector search)
- Vector search support with similarity options

**Monitoring**
- Live performance graphs (connections, ops/s, memory)
- Server stats (version, uptime, storage engine)
- Replica set status and member health

**UI**
- Compass-like sidebar with database/collection tree
- Tabbed content area
- Formatted document detail view
- Keyboard-driven with mouse support

## Installation

```bash
pip install mongotui
```

## Usage

```bash
# Interactive — shows connection screen
mongotui

# Direct connection
mongotui --uri "mongodb://admin:admin@localhost:27017/?authSource=admin"

# Short form
mongotui -u "mongodb://admin:admin@localhost:27017/?authSource=admin"
```

## Quick Start with Docker

```bash
# Start a local MongoDB instance
docker compose up -d

# Connect
mongotui -u "mongodb://admin:admin@localhost:27017/?authSource=admin"
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh |
| `Ctrl+C` | Force quit |
| `Escape` | Close modal / go back |
| `Enter` | Select / expand tree node |
| `Tab` | Switch between panels |

## Tech Stack

- **Python** 3.11+
- **Textual** — TUI framework
- **PyMongo** — MongoDB driver
- **textual-plotext** — Terminal graphs

## Requirements

- Python 3.11+
- MongoDB 4.4+ (standalone, replica set, or Atlas)

## Perfect For

- Self-hosted MongoDB deployments
- Internal infrastructure teams
- DevOps and platform engineers
- Development and staging environments
- Secure administration over SSH
- Environments where Compass can't be installed

## Development

```bash
git clone https://github.com/DevOpsPack/mongotui.git
cd mongotui
pip install -e .
mongotui
```

## License

[AGPL-3.0](LICENSE)
