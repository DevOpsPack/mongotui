# MongoTUI

<p align="center">
  <strong>A modern terminal UI for MongoDB administration</strong><br>
  Like Compass, but for your terminal.
</p>

---

[![PyPI](https://img.shields.io/pypi/v/mongotui)](https://pypi.org/project/mongotui/)
[![Python](https://img.shields.io/pypi/pyversions/mongotui)](https://pypi.org/project/mongotui/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Downloads](https://img.shields.io/pypi/dm/mongotui)](https://pypi.org/project/mongotui/)

## What is MongoTUI?

MongoTUI is a terminal-based MongoDB administration tool built with Python, Textual, and PyMongo. It provides a Compass-like experience entirely in your terminal — perfect for servers, SSH sessions, and environments where GUI tools can't be installed.

## Key Features

<div class="grid cards" markdown>

- :material-database: **Database Management**  
  Browse databases, collections, documents. Query with filters. Run aggregation pipelines.

- :material-account-group: **User Administration**  
  Create users, reset passwords, grant and revoke roles with a built-in role picker.

- :material-format-list-bulleted: **Index Management**  
  View, create, and drop indexes. Support for search indexes and vector search.

- :material-chart-line: **Live Monitoring**  
  Real-time graphs for connections, operations per second, and memory usage.

</div>

## Quick Install

```bash
pip install mongotui
```

## Quick Start

```bash
# Interactive mode
mongotui

# Direct connection
mongotui -u "mongodb://admin:admin@localhost:27017/?authSource=admin"
```

## Why MongoTUI?

| Use Case | MongoTUI | Compass | mongosh |
|----------|----------|---------|---------|
| SSH access | ✅ | ❌ | ✅ |
| Visual UI | ✅ | ✅ | ❌ |
| No install needed on server | ✅ (pip) | ❌ | ❌ |
| User management UI | ✅ | ✅ | ❌ |
| Live monitoring | ✅ | ✅ | ❌ |
| Lightweight | ✅ | ❌ | ✅ |
