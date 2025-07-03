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
    "stimulus_type": "VARCHAR(50)"
  }
}
```

The `schema_definition` field allows you to specify additional columns that will be created for storing experiment-specific data.

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
  "participant_id": "SUBJ-2024-001",
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

### Step 4: Query and Manage Data

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
       "strategy_used": "VARCHAR(100)"
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

4. **Query Results:**
   - Get all memory experiments: `GET /api/v1/experiments/?tags=memory`
   - Get specific participant data: `GET /api/v1/experiments/?participant_id=MEM-STUDY-001`
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
- Use appropriate PostGres data types (`INTEGER`, `FLOAT`, `VARCHAR`, etc.)
- Consider what data you'll need for analysis when designing schemas

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

This API includes interactive Swagger documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI**: `http://localhost:8000/openapi.json`

The Swagger UI provides:
- Interactive forms with example data
- Real-time API testing
- Schema validation
- Response examples

Use the interactive documentation to explore the API and test endpoints with sample data.

</details>