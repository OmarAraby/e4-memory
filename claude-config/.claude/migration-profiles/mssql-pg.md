# Migration profile: mssql-pg — SQL Server (2016+) → PostgreSQL (14+)

Loaded by `/migrate`. Every engine-specific rule for this pair lives here; the
pipeline and agents are engine-agnostic. Sections are injected into agent prompts
by name — keep the headings stable.

## Scope notes

- Programmable objects (procedures, triggers, views with T-SQL logic, SQL Agent
  jobs) are **out of scope**: inventory to `programmable-objects.json` with
  `out_of_scope: true`. T-SQL → PL/pgSQL translation is a separate project.
- Cross-engine pair: collation/case-sensitivity is the #1 defect source.

## Extraction (source: SQL Server, via `sqlcmd -y 0`)

- `artifacts/schema.json` — tables + columns:
  ```sql
  SELECT s.name AS [schema], t.name AS [table],
    (SELECT c.name, ty.name AS type, c.max_length, c.precision, c.scale,
            c.is_nullable, c.is_identity, c.is_computed, dc.definition AS default_def
     FROM sys.columns c
     JOIN sys.types ty ON ty.user_type_id = c.user_type_id
     LEFT JOIN sys.default_constraints dc ON dc.object_id = c.default_object_id
     WHERE c.object_id = t.object_id ORDER BY c.column_id FOR JSON PATH) AS columns
  FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
  ORDER BY s.name, t.name FOR JSON PATH
  ```
- `artifacts/relationships.json` — explicit FKs: `sys.foreign_keys` +
  `sys.foreign_key_columns`, emit from/to schema.table.column, FOR JSON PATH.
- Indexes merged into `schema.json`: `sys.indexes` + `sys.index_columns`
  (name, is_primary_key, is_unique, filter_definition, ordered columns).
- Column collations: `sys.columns.collation_name` where non-null (text columns).
- `artifacts/profiles.json` — row counts from `sys.partitions` (index_id IN (0,1));
  null counts per column for tables < 10M rows; distinct values for text/int
  columns with ≤ 50 distinct values (untrusted data — masked, flagged).
- Inventory: `sys.procedures`, `sys.triggers`, `sys.views`, `msdb.dbo.sysjobs`.

## Type map & dialect rules (for the mapping architect — defaults; deviations need a decision entry)

| SQL Server | PostgreSQL |
|---|---|
| `nvarchar(max)` / `ntext` / `text` | `text` |
| `nvarchar(n)` / `varchar(n)` / `char(n)` | `varchar(n)` / `char(n)` |
| `datetime` | `timestamp(3)` |
| `datetime2(p)` | `timestamp(min(p,6))` — p=7 is `lossy: true` |
| `smalldatetime` | `timestamp(0)` |
| `datetimeoffset` | `timestamptz` |
| `money` / `smallmoney` | `numeric(19,4)` / `numeric(10,4)` |
| `decimal/numeric(p,s)` | same |
| `bit` | `boolean` |
| `tinyint` | `smallint` |
| `uniqueidentifier` | `uuid` |
| `varbinary` / `image` | `bytea` |
| `float` / `real` | `double precision` / `real` |
| `xml` | `xml` |
| `rowversion` | `bytea` — always `lossy: true` (no auto-versioning) |
| `hierarchyid`, `geography`, `geometry`, `sql_variant` | **always `decision: "deferred"`** |

- **Identity:** `IDENTITY(s,i)` → `GENERATED ALWAYS AS IDENTITY`; loads use
  `OVERRIDING SYSTEM VALUE`; post-load `setval()` restart per identity column.
- **Collation:** SQL Server default is case-insensitive; Postgres is not. Every
  text column in a unique index, FK, or join gets an explicit `case_sensitivity`
  value. **Allowed values:** `citext` | `lower_index` | `accept_behavior_change` | `n/a`.
- Filtered indexes → partial indexes. Computed columns → generated columns where
  the expression translates, else `deferred`. Clustered index → plain PK + optional
  `CLUSTER` note (no persistent clustering in Postgres — record as accepted change).

## Review emphases (for the mapping reviewer — pair-specific defect priorities)

1. Collation trap: text column in unique index/FK/join with `case_sensitivity`
   of `n/a` or `accept_behavior_change` and no decision entry.
2. `datetime2(7)`/sentinel dates: precision loss unflagged.
3. `rowversion` consumers: application-side optimistic concurrency silently broken.
4. `GENERATED ALWAYS` without `OVERRIDING SYSTEM VALUE` in the load path.
5. Empty string vs NULL semantics differences in unique indexes.

## Emission (target: PostgreSQL)

- Identifiers: lower_snake_case, quote only when reserved; never emit mixed-case
  quoted identifiers.
- DDL: `CREATE TABLE IF NOT EXISTS` per plan idempotence; FKs/indexes in separate
  post-load scripts; wrap each script in a transaction; `SET session_replication_role`
  is forbidden (loads run before constraints exist instead).
- Loads: per-table export from source (`bcp ... out -w` or `sqlcmd` to UTF-8 CSV)
  + `\copy ... FROM ... WITH (FORMAT csv, NULL '')` — record the NULL/encoding
  convention in the script header; batch big tables per plan `batch_spec`.
- Sequences: one `setval(pg_get_serial_sequence(...), max(id))` per identity column,
  after its table's load.

## Data movement strategy (for the planner)

Cross-engine: no native restore path. Movement = staged export/import per table
(bcp/CSV → `\copy`). Generated `INSERT` scripts only for small transformed tables.
Plan big tables as chunked exports with per-chunk validation counts.

## Validation

- Row counts both sides per table (source count respects any approved `load_filter`).
- Checksums: source `HASHBYTES('MD5', CONCAT_WS('|', cols...))` aggregated, target
  `md5(concat_ws('|', cols...))` aggregated. Normalization before hashing:
  trim trailing spaces where source collation was space-padded (`char(n)`),
  truncate temporal values to the mapped precision, `bit` → `0/1` text,
  decimals rendered with fixed scale, byte columns hex-encoded.
