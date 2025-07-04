# Database Schema Documentation

## Overview

The WAVE Backend uses a PostgreSQL database with a hybrid schema design:
- **Static tables**: Fixed schema for core entities (experiment types, experiments, tags)
- **Dynamic tables**: Generated tables for experiment data based on user-defined schemas

## Static Tables

### 1. `tags` Table

Stores categorization tags for experiments.

| Column        | Type                     | Constraints                    | Description           |
| ------------- | ------------------------ | ------------------------------ | --------------------- |
| `id`          | INTEGER                  | PRIMARY KEY, AUTO_INCREMENT    | Unique identifier     |
| `name`        | VARCHAR(100)             | UNIQUE, NOT NULL, INDEXED      | Tag name              |
| `description` | TEXT                     | NULLABLE                       | Tag description       |
| `created_at`  | TIMESTAMP WITH TIME ZONE | DEFAULT now()                  | Creation timestamp    |
| `updated_at`  | TIMESTAMP WITH TIME ZONE | DEFAULT now(), ON UPDATE now() | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `name`

---

### 2. `experiment_types` Table

Defines experiment templates with schema definitions for dynamic data tables.

| Column              | Type                     | Constraints                    | Description                       |
| ------------------- | ------------------------ | ------------------------------ | --------------------------------- |
| `id`                | INTEGER                  | PRIMARY KEY, AUTO_INCREMENT    | Unique identifier                 |
| `name`              | VARCHAR(100)             | UNIQUE, NOT NULL, INDEXED      | Experiment type name              |
| `description`       | TEXT                     | NULLABLE                       | Experiment type description       |
| `table_name`        | VARCHAR(100)             | UNIQUE, NOT NULL               | Name of the dynamic data table    |
| `schema_definition` | JSON                     | NOT NULL, DEFAULT {}           | Column definitions for data table |
| `created_at`        | TIMESTAMP WITH TIME ZONE | DEFAULT now()                  | Creation timestamp                |
| `updated_at`        | TIMESTAMP WITH TIME ZONE | DEFAULT now(), ON UPDATE now() | Last update timestamp             |

**Indexes:**
- Primary key on `id`
- Unique index on `name`
- Unique index on `table_name`

**Relationships:**
- One-to-many with `experiments` table

**Schema Definition Format:**
```json
{
  "column_name": "TYPE",
  "another_column": {
    "type": "TYPE",
    "nullable": true
  }
}
```

**Supported Types:**
- `INTEGER` → PostgreSQL INTEGER
- `FLOAT` → PostgreSQL FLOAT
- `STRING` → PostgreSQL VARCHAR(255)
- `TEXT` → PostgreSQL TEXT
- `BOOLEAN` → PostgreSQL BOOLEAN
- `DATETIME` → PostgreSQL TIMESTAMP
- `JSON` → PostgreSQL JSON

---

### 3. `experiments` Table

Stores individual experiment instances that reference experiment types.

| Column               | Type                     | Constraints                                 | Description                  |
| -------------------- | ------------------------ | ------------------------------------------- | ---------------------------- |
| `uuid`               | UUID                     | PRIMARY KEY, DEFAULT uuid4(), INDEXED       | Unique identifier            |
| `experiment_type_id` | INTEGER                  | FOREIGN KEY → experiment_types.id, NOT NULL | Reference to experiment type |
| `description`        | TEXT                     | NOT NULL                                    | Experiment description       |
| `tags`               | VARCHAR(50)[]            | NULLABLE, DEFAULT []                        | Array of tag names           |
| `additional_data`    | JSON                     | NULLABLE, DEFAULT {}                        | Flexible metadata storage    |
| `created_at`         | TIMESTAMP WITH TIME ZONE | DEFAULT now()                               | Creation timestamp           |
| `updated_at`         | TIMESTAMP WITH TIME ZONE | DEFAULT now(), ON UPDATE now()              | Last update timestamp        |

**Indexes:**
- Primary key on `uuid`
- Foreign key index on `experiment_type_id`

**Relationships:**
- Many-to-one with `experiment_types` table
- One-to-many with dynamic experiment data tables (via experiment_type.table_name)

**Foreign Key Constraints:**
- `experiment_type_id` REFERENCES `experiment_types(id)`

---

## Dynamic Tables

### Experiment Data Tables

These tables are created dynamically when experiment types are created. **Each experiment type gets its own data table** based on the `table_name` field.

**Table Naming Convention:**
- Specified in `experiment_types.table_name` field
- Must be unique across all experiment types
- **One table per experiment type** (not per experiment)

**Standard Columns (Always Present):**

| Column            | Type         | Constraints                 | Description                  |
| ----------------- | ------------ | --------------------------- | ---------------------------- |
| `id`              | INTEGER      | PRIMARY KEY, AUTO_INCREMENT | Unique row identifier        |
| `experiment_uuid` | UUID         | NOT NULL, INDEXED           | Links to specific experiment |
| `participant_id`  | VARCHAR(100) | NOT NULL, INDEXED           | Participant identifier       |
| `created_at`      | TIMESTAMP    | DEFAULT now()               | Row creation timestamp       |
| `updated_at`      | TIMESTAMP    | DEFAULT now()               | Row update timestamp         |

**Custom Columns:**
- Generated from `experiment_types.schema_definition`
- Column names and types defined by users
- Support all types listed in the Type Mapping section

**Benefits of Current Design:**
- Data rows properly linked to specific experiments
- Ability to query data for individual experiments
- Proper data isolation between experiments
- Data integrity maintained via application-level validation

**Example Dynamic Table:**
```sql
-- For experiment type with table_name: "cognitive_test_data"
CREATE TABLE cognitive_test_data (
    id INTEGER PRIMARY KEY,
    experiment_uuid UUID NOT NULL,
    participant_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    reaction_time FLOAT,
    accuracy FLOAT,
    difficulty_level INTEGER,
    stimulus_type VARCHAR(255)
);
```

**Indexes:**
- Primary key on `id`
- Index on `experiment_uuid`
- Index on `participant_id`

---

## Entity Relationships

### Core Relationships

```
experiment_types (1) ←→ (many) experiments
experiment_types (1) ←→ (1) experiment_data_table
experiments (1) ←→ (many) experiment_data_rows
```

### Relationship Details

1. **ExperimentType → Experiments**
   - One experiment type can have many experiments
   - Foreign key: `experiments.experiment_type_id` → `experiment_types.id`

2. **Experiments → Experiment Data**
   - One experiment can have many data rows
   - Relationship: `experiment_data_rows.experiment_uuid` links to `experiments.uuid`
   - Data rows properly isolated per experiment
   - Multiple experiments of same type share table but data is properly segregated

3. **Tags → Experiments**
   - Many-to-many relationship via array column
   - `experiments.tags` contains array of tag names
   - No formal foreign key constraint (flexible tagging)

### Data Flow

1. **Create Experiment Type** → Creates dynamic data table
2. **Create Experiment** → References experiment type
3. **Add Data** → Inserts into dynamic table using experiment's type schema

---

## Schema Management

### Dynamic Table Creation

**Location:** `src/wave_backend/services/experiment_data.py`

**Process:**
1. Parse `schema_definition` from experiment type
2. Create standard columns (id, participant_id, timestamps)
3. Add custom columns based on schema definition
4. Execute DDL to create physical table
5. Handle both simple and complex column definitions

### Type Mapping

**Location:** `src/wave_backend/schemas/column_types.py`

```python
TYPE_MAPPING = {
    "INTEGER": Integer,
    "FLOAT": Float,
    "STRING": String(255),
    "TEXT": Text,
    "BOOLEAN": Boolean,
    "DATETIME": DateTime,
    "JSON": JSON,
}
```

### Schema Validation

**Location:** `src/wave_backend/schemas/schemas.py:112-138`

**Validation Rules:**
- Reserved column names are prohibited: `id`, `participant_id`, `created_at`, `updated_at`
- Only supported types are allowed
- Both simple and complex column definitions are supported

### Data Operations

**Available Operations:**
- `INSERT` - Add new data rows
- `SELECT` - Query data with filters
- `UPDATE` - Modify existing rows (excludes id, created_at)
- `DELETE` - Remove data rows
- `COUNT` - Count rows with filters

**Data Validation:**
- Columns must exist in target table
- Unknown columns are rejected with helpful error messages
- Type validation enforced by database constraints

---

## Migration Considerations

### Static Schema Changes
- Use standard database migration tools
- Modify models in `src/wave_backend/models/models.py`
- Update schema validation in `src/wave_backend/schemas/schemas.py`

### Dynamic Schema Changes
- No built-in migration support for dynamic tables
- Consider versioning experiment types for schema changes
- Manual ALTER TABLE operations may be required

### Backup Considerations
- Static tables: Standard PostgreSQL backup
- Dynamic tables: Ensure all experiment data tables are included in backups
- Schema definitions stored in `experiment_types.schema_definition`

---

## Performance Considerations

### Indexing Strategy
- All primary keys are indexed
- Foreign keys are indexed
- `participant_id` is indexed in dynamic tables
- Consider additional indexes based on query patterns

### Query Optimization
- Use table reflection for dynamic table operations
- Implement proper pagination for large datasets
- Consider connection pooling for concurrent access

### Scaling Considerations
- Each experiment type creates a separate table
- Large numbers of experiment types = many tables
- Consider partitioning strategies for very large datasets
