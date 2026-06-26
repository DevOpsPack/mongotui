# Quick Start

## Start MongoDB locally

```bash
docker compose up -d
```

This starts a MongoDB 7 instance with credentials `admin:admin`.

## Connect

```bash
mongotui -u "mongodb://admin:admin@localhost:27017/?authSource=admin"
```

Or run `mongotui` without arguments to get the interactive connection screen.

## Navigate

After connecting you'll see the dashboard with:

- **Sidebar** — tree navigation for databases, collections, and features
- **Tabs** — Overview, Databases, Collections, Documents, Indexes, Users, Performance

Click a database in the sidebar to see its collections. Click a collection to browse documents.

## Key actions

| Action | How |
|--------|-----|
| Browse databases | Click "Databases" in sidebar |
| View documents | Click a collection in sidebar |
| Query documents | Enter JSON filter in Documents tab, click Find |
| Create user | Go to Users tab, click Create |
| Monitor server | Click "Performance" in sidebar |
| Refresh | Press `r` |
| Quit | Press `q` or `Ctrl+C` |
