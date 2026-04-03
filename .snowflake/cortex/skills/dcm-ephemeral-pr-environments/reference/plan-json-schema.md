# plan.json Schema Reference

The `snow dcm plan --save-output` command produces `out/plan.json`. This file contains the changeset that DCM will apply.

## Top-level Structure

```json
{
  "changeset": [...],
  "metadata": {...},
  "version": "..."
}
```

## Changeset Entry Schema

Each entry in `.changeset[]`:

```json
{
  "type": "CREATE" | "ALTER" | "DROP",
  "object_id": {
    "domain": "ROLE" | "DATABASE" | "SCHEMA" | "TABLE" | "VIEW" | "DYNAMIC_TABLE" | "STAGE" | "TASK" | "PROCEDURE" | ...,
    "name": "OBJECT_NAME",
    "fqn": "DB.SCHEMA.OBJECT_NAME"
  },
  "changes": [...]
}
```

## Common jq Queries

### Count operations by type
```bash
jq '[.changeset[] | select(.type == "CREATE")] | length' out/plan.json
jq '[.changeset[] | select(.type == "ALTER")] | length' out/plan.json
jq '[.changeset[] | select(.type == "DROP")] | length' out/plan.json
```

### List object domains for a specific operation type
```bash
jq -r '[.changeset[] | select(.type == "CREATE") | .object_id.domain] | unique | .[]' out/plan.json
```

### Count operations by type and domain
```bash
jq --arg OP "CREATE" --arg DOM "TABLE" \
  '[.changeset[] | select(.type == $OP and .object_id.domain == $DOM)] | length' out/plan.json
```

### Find destructive DROP operations on critical objects
```bash
jq -c '[.changeset[] | select(.type == "DROP" and (.object_id.domain | IN("DATABASE", "SCHEMA", "TABLE", "STAGE")))]' out/plan.json
```

### List all object FQNs being created
```bash
jq -r '.changeset[] | select(.type == "CREATE") | .object_id.fqn' out/plan.json
```
