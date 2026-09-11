# Migration profile: mssql-mssql — SQL Server → SQL Server (instance/version move)

Loaded by `/migrate`. Same-dialect pair: the type map is near-identity, but this is
NOT a subset of a cross-engine migration — programmable objects enter scope, version
feature gaps matter, and native movement usually beats generated scripts.

## Scope notes

- Programmable objects are **in scope**: procedures, triggers, views, functions are
  scripted from the source and reviewed (same dialect — copy with review, not
  translation). SQL Agent jobs are scripted + inventoried; re-creation on the target
  is a runbook step. Cross-database references are flagged as decisions.
- Record at init: source and target `@@VERSION`, edition, and compatibility level —
  the version gap drives the review emphases.

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
  `sys.foreign_key_columns`, FOR JSON PATH.
- Indexes merged into `schema.json`: `sys.indexes` + `sys.index_columns`
  (incl. filter_definition, compression, partition scheme).
- Column + database collations (`sys.columns.collation_name`,
  `DATABASEPROPERTYEX(..., 'Collation')`) — cross-instance collation mismatch is
  this pair's collation trap.
- **Edition/feature usage:** `sys.dm_db_persisted_sku_features` (features that block
  restore onto a lesser edition), `sys.partition_schemes`, compression settings.
- `artifacts/profiles.json` — row counts, null counts, low-cardinality distincts
  (same rules as any profile: untrusted data, masked).
- Programmable objects: scripted via `sys.sql_modules` into
  `artifacts/programmable-objects.json` with `out_of_scope: false`.

## Type map & dialect rules (for the mapping architect)

- Default: **identity mapping** — every type maps to itself. A deviation is the
  exception and always carries a decision entry:

| Source | Target | When |
|---|---|---|
| `text` / `ntext` / `image` | `varchar(max)` / `nvarchar(max)` / `varbinary(max)` | deprecated types — recommend conversion, `decision` entry required |
| `datetime` | `datetime2(3)` | only if the user opts into modernization — otherwise keep |
| anything edition-gated | same | `deferred` if the target edition lacks the feature (per `sku_features`) |

- **Identity:** stays `IDENTITY`; loads use `SET IDENTITY_INSERT <table> ON/OFF`;
  post-load `DBCC CHECKIDENT (<table>, RESEED)` per identity column.
- **Collation:** per text column where source and target collations differ —
  **allowed values:** `keep-source-collation` (explicit `COLLATE` clause) |
  `adopt-target-collation` | `accept_behavior_change` | `n/a`.
- Partitioning, compression, filtered indexes: carry over verbatim when the target
  edition supports them; otherwise `deferred` with the edition gap named.

## Review emphases (for the mapping reviewer)

1. Cross-instance collation mismatch on join/index columns without an explicit
   collation decision (breaks joins and unique semantics silently).
2. Edition/version gap: mapped feature absent on target edition
   (check against the extracted `sku_features` list).
3. Deprecated types carried over without a decision entry.
4. `IDENTITY_INSERT` discipline: missing ON/OFF pairing or missing RESEED.
5. Cross-database / linked-server references inside in-scope programmable objects.

## Emission (target: SQL Server)

- Identifiers: preserve source names and casing exactly; bracket-quote `[...]`.
- DDL: `IF OBJECT_ID(...) IS NULL` guards per plan idempotence; `SET XACT_ABORT ON`
  + explicit transactions per script; FKs/indexes in post-load scripts.
- Loads: `SET IDENTITY_INSERT ON` → batched insert → `OFF` → `DBCC CHECKIDENT RESEED`,
  in that order, per table with an identity.
- Programmable objects: emit scripted modules in dependency order into
  `scripts/modules/*.sql`; these go through the SQL reviewer like everything else.

## Data movement strategy (for the planner)

Prefer native paths — generated row-by-row scripts are the last resort:
1. **Whole database, no transforms:** `BACKUP/RESTORE` (or detach/attach) — the
   pipeline then only verifies (stages 10–13); mapping drives the *verification*, not
   the movement. Say so explicitly in the plan.
2. **Table-level moves / partial transforms:** `bcp out` / `BULK INSERT` or SSIS-free
   `bcp`-pair per table, batched per plan.
3. **Small transformed tables:** generated `INSERT ... SELECT` via linked server —
   flag the linked-server security surface in the runbook.

## Validation

- Row counts both sides; source counts respect approved `load_filter`s.
- Same-dialect checksums both sides: `CHECKSUM_AGG(BINARY_CHECKSUM(cols...))` for
  speed, `HASHBYTES('MD5', CONCAT_WS('|', cols...))` aggregated for rigor on
  flagged tables. Columns with a collation change compare under an explicit
  `COLLATE` to make the comparison deterministic.
- Programmable objects: definition diff (normalized whitespace) source vs target.
