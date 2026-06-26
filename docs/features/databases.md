# Database Management

## Browsing

Click **Databases** in the sidebar to see all databases with:

- Collection count
- Data size (MB)
- Storage size (MB)

Click a specific database to expand and see its collections.

## Creating a database

Click **Create DB** in the Databases tab. Enter:

- Database name
- Initial collection name (required — MongoDB creates a database when its first collection is created)

## Dropping a database

Select a database in the table and click **Drop DB**. Confirm the deletion.

!!! warning
    Dropping a database permanently deletes all collections and documents within it.

## Collections

Click a database in the sidebar to see its collections with:

- Document count
- Size (KB)

## Documents

Click a collection to browse its documents. The Documents tab shows:

- First 50 documents in a table
- A JSON filter input for querying
- Click a row to see the full formatted document

### Filtering

Enter a JSON filter and click **Find**:

```json
{"status": "active", "age": {"$gte": 21}}
```

Leave empty to show all documents.
