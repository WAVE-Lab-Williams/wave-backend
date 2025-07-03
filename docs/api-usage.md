The WAVE Backend API is a FastAPI application designed for managing psychology and behavioral experiments. It provides a RESTful interface for creating experiment types, managing tags, and conducting experiments with structured data collection.

<details>
<summary><strong>Core Concepts</strong></summary>

### 1. Experiment Types
Experiment types define the structure and schema for different kinds of experiments. They act as templates that specify:
- What kind of data will be collected
- The database schema for storing results
- Metadata about the experiment methodology

### 2. Tags
Tags are used to categorize and organize experiments. They enable:
- Filtering experiments by research area (e.g., "cognitive", "memory", "attention")
- Grouping related experiments across different types
- Searchable metadata for data analysis

### 3. Experiments
Experiments are individual instances or runs of a specific experiment type. Each experiment:
- References an experiment type (defines the structure)
- Contains participant information
- Stores experimental data and results
- Can be tagged for organization

</details>

<details>
<summary><strong>API Workflow</strong></summary>

### Step 1: Create Experiment Types (Required First)

Before creating experiments, you must define the experiment types that will be used.

**POST `/api/v1/experiment-types/`**

```json
{
  "name": "cognitive_assessment",
  "description": "Cognitive performance evaluation with reaction time measurements",
  "table_name": "cognitive_test_data",
  "schema_definition": {
    "reaction_time": "FLOAT",
    "accuracy": "FLOAT", 
    "difficulty_level": "INTEGER",
    "stimulus_type": "STRING"
  }
}
```

The `schema_definition` field allows you to specify additional columns that will be created for storing experiment-specific data.

**Supported Column Types:**
- `INTEGER` - Whole numbers
- `FLOAT` - Decimal numbers  
- `STRING` - Text (up to 255 characters)
- `TEXT` - Long text
- `BOOLEAN` - True/false values
- `DATETIME` - Date and time values
- `JSON` - JSON objects

**Note:** When you create an experiment type, a dedicated database table is automatically created with your custom columns plus these required columns: `id`, `participant_id`, `created_at`, `updated_at`.

### Step 2: Create Tags (Optional)

Create tags to categorize your experiments. This step is optional but recommended for organization.

**POST `/api/v1/tags/`**

```json
{
  "name": "cognitive",
  "description": "Cognitive performance and mental processing experiments"
}
```

Common tag examples:
- `cognitive` - Mental processing experiments
- `memory` - Memory-related studies
- `attention` - Attention and focus studies
- `behavioral` - Behavioral response experiments
- `visual` - Visual perception studies
- `audio` - Auditory processing experiments

### Step 3: Create Experiments

Once you have experiment types defined, you can create individual experiment instances.

**POST `/api/v1/experiments/`**

```json
{
  "experiment_type_id": 1,
  "description": "Cognitive assessment with visual stimuli for participant 001",
  "tags": ["cognitive", "visual", "attention"],
  "additional_data": {
    "session_duration": 30,
    "difficulty_level": 2,
    "baseline_score": 85,
    "notes": "First session, participant was alert and cooperative"
  }
}
```

### Step 4: Add Experiment Data

Once you have created experiments, you can add actual data rows to the experiment's custom table.

**POST `/api/v1/experiment-data/{experiment_id}/data/`**

```json
{
  "participant_id": "SUBJ-2024-001",
  "data": {
    "reaction_time": 1.23,
    "accuracy": 0.85,
    "difficulty_level": 2,
    "stimulus_type": "visual"
  }
}
```

This creates a new row in the experiment type's data table with the custom columns you defined.

**Get Experiment Data**

**GET `/api/v1/experiment-data/{experiment_id}/data/`**

Supports filtering by:
- `participant_id` - Filter by participant  
- `created_after` - Filter by creation date (after)
- `created_before` - Filter by creation date (before)
- `limit` and `offset` - Pagination

**Update Experiment Data**

**PUT `/api/v1/experiment-data/{experiment_id}/data/row/{row_id}`**

```json
{
  "participant_id": "SUBJ-2024-001",
  "data": {
    "reaction_time": 1.45,
    "accuracy": 0.90
  }
}
```

**Query Experiment Data**

**POST `/api/v1/experiment-data/{experiment_id}/data/query`**

```json
{
  "participant_id": "SUBJ-2024-001",
  "filters": {
    "difficulty_level": 2,
    "accuracy": 0.85
  },
  "created_after": "2024-01-01T00:00:00",
  "limit": 100,
  "offset": 0
}
```

### Step 5: Query and Manage Experiments

#### Get All Experiments
**GET `/api/v1/experiments/`**

Supports filtering by:
- `experiment_type_id` - Filter by experiment type
- `participant_id` - Filter by participant
- `tags` - Filter by tags
- `skip` and `limit` - Pagination

Example: `GET /api/v1/experiments/?tags=cognitive&tags=memory&limit=50`

#### Get Specific Experiment
**GET `/api/v1/experiments/{experiment_uuid}`**

#### Get Experiment Schema Information
**GET `/api/v1/experiments/{experiment_uuid}/columns`**

Returns the database schema for the experiment, including both base columns and any custom columns defined in the experiment type.

</details>

<details>
<summary><strong>Data Flow Example</strong></summary>

Here's a complete workflow for a memory study:

1. **Create Experiment Type:**
   ```json
   {
     "name": "word_recall_test",
     "description": "Memory test using word list recall",
     "table_name": "word_recall_data",
     "schema_definition": {
       "word_list_length": "INTEGER",
       "recall_accuracy": "FLOAT",
       "recall_time": "FLOAT",
       "strategy_used": "STRING"
     }
   }
   ```

2. **Create Tags:**
   ```json
   [
     {"name": "memory", "description": "Memory-related experiments"},
     {"name": "recall", "description": "Recall-based memory tests"},
     {"name": "verbal", "description": "Verbal/language-based tasks"}
   ]
   ```

3. **Run Experiments:**
   ```json
   {
     "experiment_type_id": 1,
     "participant_id": "MEM-STUDY-001",
     "description": "Word recall test - 20 word list",
     "tags": ["memory", "recall", "verbal"],
     "additional_data": {
       "word_list_length": 20,
       "session_time": "morning",
       "participant_age": 25,
       "notes": "Participant used visualization strategy"
     }
   }
   ```

4. **Add Experiment Data:**
   ```json
   {
     "participant_id": "MEM-STUDY-001",
     "data": {
       "word_list_length": 20,
       "recall_accuracy": 0.75,
       "recall_time": 45.2,
       "strategy_used": "visualization"
     }
   }
   ```

5. **Query Results:**
   - Get all memory experiments: `GET /api/v1/experiments/?tags=memory`
   - Get specific participant data: `GET /api/v1/experiments/?participant_id=MEM-STUDY-001`
   - Get experiment data: `GET /api/v1/experiment-data/{experiment_id}/data/?participant_id=MEM-STUDY-001`
   - Query data with filters: `POST /api/v1/experiment-data/{experiment_id}/data/query` with custom filters
   - Get schema info: `GET /api/v1/experiments/{uuid}/columns`

</details>

<details>
<summary><strong>Best Practices</strong></summary>

### Naming Conventions
- **Experiment Types**: Use descriptive names like `cognitive_assessment`, `memory_recall_test`
- **Participant IDs**: Use consistent formats like `SUBJ-2024-001`, `PART-COGNITIVE-123`
- **Tags**: Use lowercase, single words when possible (`memory`, `cognitive`, `visual`)

### Data Organization
- Plan your experiment types before starting data collection
- Use tags consistently across experiments for better filtering
- Include meaningful descriptions for both experiments and experiment types
- Store metadata in `additional_data` for flexibility

### Schema Design
- Define custom columns in experiment type `schema_definition` for structured data
- Use appropriate data types: `INTEGER`, `FLOAT`, `STRING`, `TEXT`, `BOOLEAN`, `DATETIME`, `JSON`
- Consider what data you'll need for analysis when designing schemas
- Remember that each experiment type gets its own dedicated table for data storage
- Always include participant_id when adding data rows - it's required for all experiment data

</details>

<details>
<summary><strong>Error Handling</strong></summary>

The API returns standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation errors, missing required fields)
- `404` - Not Found (experiment, experiment type, or tag doesn't exist)
- `500` - Internal Server Error

Common validation errors:
- Missing required fields
- Invalid `experiment_type_id` (must reference existing experiment type)
- Invalid data types in request body
- Duplicate names (experiment types and tags must be unique)

</details>

<details>
<summary><strong>Interactive Documentation</strong></summary>

**Available Documentation Endpoints:**
- `/docs` - Interactive Swagger UI
- `/redoc` - Alternative ReDoc interface
- `/openapi.json` - OpenAPI specification

The Swagger UI provides:
- Interactive forms with example data
- Real-time API testing
- Schema validation
- Response examples

Use the interactive documentation to explore the API and test endpoints with sample data.

</details>