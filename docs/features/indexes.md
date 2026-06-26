# Index Management

## Viewing indexes

Select a collection from the sidebar. Navigate to the **Indexes** tab to see:

- Index name
- Keys and direction
- Unique flag
- Size (KB)
- Total index size for the collection

## Creating an index

Click **Create** and enter fields in the format:

```
name:1,age:-1
```

- `1` = ascending
- `-1` = descending

Optionally set as unique.

## Dropping an index

Select an index and click **Drop**.

!!! note
    The `_id_` index cannot be dropped.

## Search Indexes

MongoTUI supports creating Atlas Search and Vector Search indexes.

### Text search index

Click **+ Search** and configure:

- **Index name**
- **Index type**: Search (text)
- **Mapping**: Dynamic (all fields) or Static (specify fields)
- **Analyzer**: defaults to `lucene.standard`

### Vector search index

Click **+ Search** and configure:

- **Index type**: Vector Search
- **Vector field**: the field containing embeddings (e.g. `embedding`)
- **Dimensions**: vector size (e.g. `1536` for OpenAI, `768` for Cohere)
- **Similarity**: `cosine`, `euclidean`, or `dotProduct`
- **Filter fields**: optional fields for pre-filtering results

### Dropping search indexes

Select a search index in the lower table and click **x Search**.
