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

**Note:** When you create an experiment type, a dedicated database table is automatically created with your custom columns plus these required columns: `id`, `experiment_uuid`, `participant_id`, `created_at`, `updated_at`.

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

**Response:**
```json
{
  "id": 1,
  "experiment_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "participant_id": "SUBJ-2024-001",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "reaction_time": 1.23,
  "accuracy": 0.85,
  "difficulty_level": 2,
  "stimulus_type": "visual"
}
```

**Get Experiment Data**

**GET `/api/v1/experiment-data/{experiment_id}/data/`**

Supports filtering by:
- `participant_id` - Filter by participant  
- `created_after` - Filter by creation date (after)
- `created_before` - Filter by creation date (before)
- `limit` and `offset` - Pagination

**Response:**
```json
[
  {
    "id": 1,
    "experiment_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "participant_id": "SUBJ-2024-001",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "reaction_time": 1.23,
    "accuracy": 0.85,
    "difficulty_level": 2,
    "stimulus_type": "visual"
  },
  {
    "id": 2,
    "experiment_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "participant_id": "SUBJ-2024-002",
    "created_at": "2024-01-15T11:45:00Z",
    "updated_at": "2024-01-15T11:45:00Z",
    "reaction_time": 1.45,
    "accuracy": 0.92,
    "difficulty_level": 3,
    "stimulus_type": "audio"
  }
]
```

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

**Response:**
```json
{
  "id": 1,
  "experiment_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "participant_id": "SUBJ-2024-001",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:22:00Z",
  "reaction_time": 1.45,
  "accuracy": 0.90,
  "difficulty_level": 2,
  "stimulus_type": "visual"
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

### Step 5: Search and Query Data

The API provides powerful search capabilities to find experiments, data, and metadata across your research database.

#### Basic Experiment Queries
**GET `/api/v1/experiments/`**

Supports filtering by:
- `experiment_type_id` - Filter by experiment type
- `participant_id` - Filter by participant
- `tags` - Filter by tags
- `skip` and `limit` - Pagination

Example: `GET /api/v1/experiments/?tags=cognitive&tags=memory&limit=50`

#### Advanced Search Capabilities

##### Search Experiments by Tags
**POST `/api/v1/search/experiments/by-tags`**

Find experiments based on tag criteria with flexible matching:

```json
{
  "tags": ["cognitive", "memory"],
  "match_all": true,
  "created_after": "2024-01-01T00:00:00Z",
  "skip": 0,
  "limit": 100
}
```

- `match_all: true` - Experiments must have ALL specified tags
- `match_all: false` - Experiments must have ANY of the specified tags

##### Search Experiment Types by Description
**POST `/api/v1/search/experiment-types/by-description`**

Find experiment types using text search in names and descriptions:

```json
{
  "search_text": "reaction time",
  "created_after": "2024-01-01T00:00:00Z",
  "skip": 0,
  "limit": 100
}
```

##### Search Tags by Name
**POST `/api/v1/search/tags/by-name`**

Find tags by searching names and descriptions:

```json
{
  "search_text": "cognitive",
  "skip": 0,
  "limit": 100
}
```

##### Search Experiments Within Type
**POST `/api/v1/search/experiments/by-description-and-type`**

Search experiment descriptions within a specific experiment type:

```json
{
  "experiment_type_id": 1,
  "search_text": "visual stimuli",
  "skip": 0,
  "limit": 100
}
```

##### Advanced Multi-Criteria Search
**POST `/api/v1/search/experiments/advanced`**

Combine multiple search criteria:

```json
{
  "search_text": "reaction time",
  "tags": ["cognitive", "visual"],
  "match_all_tags": false,
  "experiment_type_id": 1,
  "created_after": "2024-01-01T00:00:00Z",
  "skip": 0,
  "limit": 100
}
```

##### Get Experiment Data by Tags
**POST `/api/v1/search/experiment-data/by-tags`**

Retrieve all experiment data for experiments matching specific tags:

```json
{
  "tags": ["memory", "recall"],
  "match_all": true,
  "created_after": "2024-01-01T00:00:00Z",
  "skip": 0,
  "limit": 500
}
```

**Response includes:**
```json
{
  "data": [
    {
      "id": 1,
      "experiment_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "participant_id": "SUBJ-2024-001",
      "reaction_time": 1.23,
      "accuracy": 0.85,
      "experiment_metadata": {
        "experiment_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "experiment_description": "Cognitive assessment with visual stimuli",
        "experiment_type_name": "cognitive_assessment",
        "experiment_tags": ["cognitive", "memory"]
      }
    }
  ],
  "total_rows": 150,
  "total_experiments": 5,
  "experiment_info": {
    "550e8400-e29b-41d4-a716-446655440000": {
      "description": "Cognitive assessment with visual stimuli",
      "type_name": "cognitive_assessment",
      "tags": ["cognitive", "memory"],
      "data_count": 30
    }
  },
  "pagination": {
    "skip": 0,
    "limit": 500,
    "total": 150
  }
}
```

#### Individual Experiment Management

##### Get Specific Experiment
**GET `/api/v1/experiments/{experiment_uuid}`**

##### Get Experiment Schema Information
**GET `/api/v1/experiments/{experiment_uuid}/columns`**

Returns the database schema for the experiment, including both base columns and any custom columns defined in the experiment type.

#### Search Features

All search endpoints support:
- **Date filtering**: `created_after` and `created_before` parameters
- **Pagination**: `skip` and `limit` parameters  
- **Case-insensitive text search**: Partial matching in descriptions and names
- **Data isolation**: Results are properly isolated between experiments
- **Rich metadata**: Search results include experiment context and metadata

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

3. **Create Experiments:**
   ```json
   {
     "experiment_type_id": 1,
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

5. **Query and Search Results:**
   - **Basic queries:**
     - Get all memory experiments: `GET /api/v1/experiments/?tags=memory`
     - Get specific participant data: `GET /api/v1/experiments/?participant_id=MEM-STUDY-001`
     - Get experiment data: `GET /api/v1/experiment-data/{experiment_id}/data/?participant_id=MEM-STUDY-001`
     - Query data with filters: `POST /api/v1/experiment-data/{experiment_id}/data/query` with custom filters
     - Get schema info: `GET /api/v1/experiments/{uuid}/columns`
   
   - **Advanced search:**
     - Find all memory-related experiments: `POST /api/v1/search/experiments/by-tags` with `{"tags": ["memory"]}`
     - Search for recall experiments: `POST /api/v1/search/experiment-types/by-description` with `{"search_text": "recall"}`
     - Get combined data from all memory experiments: `POST /api/v1/search/experiment-data/by-tags` with `{"tags": ["memory"]}`
     - Search within word recall experiments: `POST /api/v1/search/experiments/by-description-and-type` with `{"experiment_type_id": 1, "search_text": "20 word"}`

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

<details>
<summary><strong>API Versioning & Client Compatibility</strong></summary>

The WAVE Backend API implements automatic version compatibility checking between client libraries and the server. This ensures smooth operation across different client and server versions while providing warnings for potential incompatibilities.

### How Versioning Works

**1. Version Headers**
- **Client Request**: Include `X-WAVE-Client-Version` header with your client library version
- **Server Response**: All responses include `X-WAVE-API-Version` header with current API version
- **Example**: `X-WAVE-Client-Version: 1.0.0` → Server responds with `X-WAVE-API-Version: 1.0.1`

**2. Compatibility Rules (Semantic Versioning)**
- ✅ **Compatible**: Same major version (1.0.0 ↔ 1.5.0)
- ❌ **Incompatible**: Different major versions (1.0.0 ↔ 2.0.0)
- **Forward Compatible**: Older clients work with newer API minor/patch versions
- **Backward Compatible**: Newer minor/patch versions work with older APIs

**3. Non-Blocking Warnings**
- Incompatible versions generate server-side log warnings
- Requests are never blocked due to version mismatches
- Graceful degradation ensures continued operation

### Version Information Endpoint

**GET `/version`**

Get detailed version compatibility information:

```bash
curl -H "X-WAVE-Client-Version: 1.0.0" http://localhost:8000/version
```

**Response (Compatible Versions):**
```json
{
  "api_version": "1.0.1",
  "client_version": "1.0.0",
  "compatible": true,
  "compatibility_rule": "Semantic versioning: same major version = compatible"
}
```

**Response (Incompatible Versions):**
```json
{
  "api_version": "2.0.0",
  "client_version": "1.0.0",
  "compatible": false,
  "compatibility_rule": "Semantic versioning: same major version = compatible",
  "warning": "Major version mismatch: Client v1.0.0 may not be compatible with API v2.0.0. Consider upgrading your client library."
}
```

**Response (No Client Version Header):**
```json
{
  "api_version": "1.0.0",
  "client_version": null,
  "compatibility_rule": "Semantic versioning: same major version = compatible",
  "message": "No client version provided. Add X-WAVE-Client-Version header for compatibility checking."
}
```

### Client Implementation Examples

**Python (requests library):**
```python
import requests

headers = {"X-WAVE-Client-Version": "1.0.0"}
response = requests.get("http://localhost:8000/api/v1/experiments/", headers=headers)

# Check API version in response
api_version = response.headers.get("X-WAVE-API-Version")
print(f"API Version: {api_version}")
```

**JavaScript (fetch API):**
```javascript
const headers = {
  "X-WAVE-Client-Version": "1.0.0",
  "Content-Type": "application/json"
};

fetch("http://localhost:8000/api/v1/experiments/", { headers })
  .then(response => {
    console.log("API Version:", response.headers.get("X-WAVE-API-Version"));
    return response.json();
  });
```

**cURL:**
```bash
curl -H "X-WAVE-Client-Version: 1.0.0" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/experiments/
```

### Version Compatibility Matrix

| Client Version | API Version | Compatible | Notes                    |
| -------------- | ----------- | ---------- | ------------------------ |
| 1.0.0          | 1.0.0       | ✅          | Exact match              |
| 1.0.0          | 1.0.1       | ✅          | Patch update             |
| 1.0.0          | 1.1.0       | ✅          | Minor update             |
| 1.2.0          | 1.0.0       | ✅          | Client ahead (minor)     |
| 1.0.0          | 2.0.0       | ❌          | Major version difference |
| 2.1.0          | 1.9.0       | ❌          | Different major versions |

### CORS Support

The versioning headers are automatically exposed for browser-based clients:
- `Access-Control-Expose-Headers` includes `X-WAVE-API-Version`
- Cross-origin requests can access version information
- No additional CORS configuration needed

### Monitoring & Logging

**Server-side logging automatically tracks:**
- Version compatibility status for all requests
- Client library adoption across your user base
- Potential compatibility issues before they become problems

**Log Examples:**
```
INFO: Compatible versions: Client v1.0.0, API v1.0.1
WARNING: Version compatibility: Major version mismatch: Client v1.0.0 may not be compatible with API v2.0.0...
DEBUG: User agent: wave-python-client/1.0.0
```

</details>