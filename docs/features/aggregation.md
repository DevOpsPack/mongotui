# Aggregation Pipelines

## Running a pipeline

1. Select a collection from the sidebar
2. Navigate to the **Aggregation** tab
3. Enter a pipeline as a JSON array
4. Click **Run Pipeline**

## Examples

### Count by field

```json
[{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
```

### Filter and project

```json
[
  {"$match": {"age": {"$gte": 21}}},
  {"$project": {"name": 1, "age": 1, "_id": 0}}
]
```

### Top 5 by score

```json
[
  {"$sort": {"score": -1}},
  {"$limit": 5}
]
```

### Lookup (join)

```json
[
  {"$lookup": {
    "from": "orders",
    "localField": "_id",
    "foreignField": "userId",
    "as": "orders"
  }},
  {"$project": {"name": 1, "orderCount": {"$size": "$orders"}}}
]
```

### Unwind arrays

```json
[
  {"$unwind": "$tags"},
  {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
  {"$sort": {"count": -1}}
]
```

## Notes

- Results are limited to 100 rows in the display
- The pipeline runs on the currently selected collection
- Supports all standard MongoDB aggregation stages
