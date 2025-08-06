# WAVE Backend Authentication System

This document provides a comprehensive guide to the WAVE backend's secure two-key authentication system using Unkey's API v2.

## Overview

The WAVE backend implements a secure dual-key authentication system that separates backend validation capabilities from user access permissions. This architecture ensures that user API keys cannot be used to validate other keys, providing defense in depth against key compromise.

## First-Time Unkey Setup

### 1. Create a Unkey Account and Workspace

1. Sign up at [unkey.com](https://unkey.com)
2. Create a new workspace for your WAVE project
3. Note your workspace ID for reference

### 2. Create the Four Required Roles

Navigate to your workspace settings and create these roles with the following hierarchy:

1. **admin** (highest privilege level)
2. **test** (testing and system operations)
3. **researcher** (experiment creation and data access)
4. **experimentee** (basic data submission access)

The system implements hierarchical permissions where higher roles can access lower-level endpoints.

### 3. Create the Root Validator Key

This is the critical backend authentication key:

1. Go to "API Keys" in your workspace
2. Create a new API key named "ROOT_VALIDATOR_KEY" or "Backend Validator"
3. **Important**: Grant it the `api.*.verify_key` permission (this allows it to validate other keys)
4. Set no expiration (or a very long expiration for production)
5. No rate limiting needed for backend use
6. Copy this key and store it securely as `ROOT_VALIDATOR_KEY` in your backend environment

### 4. Create User API Keys

For each user, client, or service that needs access:

1. Create a new API key with a descriptive name (e.g., "John Doe - Researcher", "Mobile App - Production")
2. Assign the appropriate role (experimentee, researcher, test, or admin)
3. **Critical**: Do NOT grant `api.*.verify_key` permission to user keys
4. Optional settings:
   - **Rate Limiting**: Set requests per minute/hour based on expected usage
   - **Expiration**: Set key expiration dates for temporary access or security policies
   - **IP Restrictions**: Limit keys to specific IP ranges if needed

### 5. Development Key Setup

For development and testing:

1. Create a user key with `test` role named "Development Key"
2. No `api.*.verify_key` permission
3. Store as `WAVE_API_KEY` in your development environment
4. Consider setting a reasonable expiration (e.g., 90 days) and rate limits

## Architecture

### Two-Key System

The authentication system uses two distinct types of API keys:

#### 1. ROOT_VALIDATOR_KEY (Backend Secret)

- **Purpose**: Authenticates the backend service to Unkey's API
- **Storage**: Backend environment variable (`ROOT_VALIDATOR_KEY`)
- **Permissions**: Has `api.*.verify_key` permission in Unkey workspace
- **Usage**: Used in Authorization header when calling Unkey's validation API
- **Security**: Never exposed to clients, stays secure on backend servers
- **Scope**: Cannot and should not be used for user operations

#### 2. User API Keys (Client Tokens)

- **Purpose**: Provide authenticated access to WAVE API endpoints
- **Distribution**: Given to users/clients (e.g., `WAVE_API_KEY` for development)
- **Permissions**: Role-based permissions (experimentee, researcher, test, admin)
- **Restrictions**: Do NOT have `api.*.verify_key` permission
- **Usage**: Sent by clients in `Authorization: Bearer` headers
- **Validation**: Placed in request body when backend calls Unkey for validation

### Role Hierarchy

The system implements a hierarchical role system:

```
ADMIN (4) ≥ TEST (3) ≥ RESEARCHER (2) ≥ EXPERIMENTEE (1)
```

Higher-level roles can access endpoints requiring lower-level permissions.

## Security Model

### Key Separation

The dual-key architecture provides several security benefits:

1. **Isolation**: User keys cannot validate other keys
2. **Least Privilege**: Each key type has only the permissions it needs
3. **Compromise Containment**: If a user key is compromised, it cannot perform validation operations
4. **Backend Security**: Root validation key remains secure on backend infrastructure

### Permission Structure

```mermaid
graph TD
    A[Client Request] --> B[WAVE Backend]
    B --> C{Extract User Key}
    C --> D[Call Unkey API]
    D --> E[Authorization: ROOT_VALIDATOR_KEY]
    D --> F[Body: user_api_key]
    F --> G[Unkey Validation]
    G --> H[Return User Permissions]
    H --> I[Authorization Decision]
    I --> J[Allow/Deny Request]
```

## Configuration

### Required Environment Variables

```bash
# Backend root key for Unkey API authentication
ROOT_VALIDATOR_KEY=sk_root_1234...

# User API key for development/testing  
WAVE_API_KEY=sk_user_5678...
```

### Optional Configuration

```bash
# Authentication cache TTL in seconds (default: 300)
WAVE_AUTH_CACHE_TTL=300

# Unkey API base URL (default: https://api.unkey.com/v2)
WAVE_AUTH_BASE_URL=https://api.unkey.com/v2

# HTTP request timeout in seconds (default: 10.0)
WAVE_AUTH_TIMEOUT=10.0
```

## Authentication Flow

### Step-by-Step Process

1. **Client Request**:
   ```http
   GET /api/experiments
   Authorization: Bearer sk_user_1234567890abcdef
   ```

2. **Backend Extraction**:
   - FastAPI dependency extracts `sk_user_1234567890abcdef`
   - Check TTL-based cache first for performance

3. **Unkey API Call** (if not cached):
   ```http
   POST https://api.unkey.com/v2/keys.verifyKey
   Authorization: Bearer sk_root_validation_key
   Content-Type: application/json
   
   {
     "key": "sk_user_1234567890abcdef"
   }
   ```

4. **Unkey Response**:
   ```json
   {
     "meta": {
       "requestId": "req_abc123"
     },
     "data": {
       "valid": true,
       "keyId": "key_user123",
       "roles": ["researcher"],
       "permissions": ["read:experiments", "write:experiments"]
     }
   }
   ```

5. **Authorization Decision**:
   - Extract role from response (`researcher`)
   - Check if role meets endpoint requirements
   - Allow request if authorized, return 401/403 if not

6. **Caching**:
   - Cache successful validation for TTL duration
   - Use composite cache key: `user_key:required_role`

### Error Handling

- **Invalid User Key**: Return 401 Unauthorized
- **Insufficient Permissions**: Return 403 Forbidden  
- **Network Errors**: Return 503 Service Unavailable
- **Malformed Responses**: Log error, return 500 Internal Server Error

## API Usage

### Decorator Usage

```python
from wave_backend.auth.decorator import auth
from wave_backend.auth.roles import Role

# Any valid API key
@router.get("/public-data")
@auth.any
async def get_public_data(
    auth: tuple[str, Optional[Role]]  # Injected by decorator
):
    key_id, role = auth
    # Process request with user's role context

# Specific role requirement
@router.post("/experiments")
@auth.role(Role.RESEARCHER)
async def create_experiment(
    experiment: ExperimentCreate,
    auth: tuple[str, Role]  # Guaranteed role
):
    key_id, role = auth
    # User guaranteed to have RESEARCHER role or higher
```

### Direct Client Usage

```python
from wave_backend.auth.unkey_client import get_unkey_client
from wave_backend.auth.roles import Role

# Get cached client instance
client = get_unkey_client()

# Validate user key
result = await client.validate_key(
    key="sk_user_key_from_request",
    required_role=Role.RESEARCHER
)

if result.valid:
    print(f"User role: {result.role}")
    print(f"Key ID: {result.key_id}")
else:
    print(f"Validation failed: {result.error}")
```

## Testing

### Test Environment Setup

The testing system provides fixtures for both integration and unit testing:

```python
# Large/integration tests - requires real keys
@pytest.fixture
def real_unkey_client() -> UnkeyClient:
    """UnkeyClient configured with ROOT_VALIDATOR_KEY."""
    
@pytest.fixture  
def user_api_key() -> str:
    """Real user API key from WAVE_API_KEY environment."""

# Small/unit tests - uses mocks
@pytest.fixture
def unkey_client():
    """Mocked UnkeyClient for unit testing."""
    
@pytest.fixture
def mock_unkey_client():
    """Mock client with configurable responses."""
```

### Cross-Validation Testing

Test the two-key system interaction:

```python
@pytest.mark.asyncio
async def test_cross_validation(real_unkey_client, user_api_key):
    """Test ROOT_VALIDATOR_KEY validating WAVE_API_KEY."""
    result = await real_unkey_client.validate_key(user_api_key)
    
    assert result.valid is True
    assert result.role is not None
    assert result.key_id is not None
```

### Running Tests

```bash
# Unit tests (no real API calls)
make test-small

# Integration tests (requires real keys)  
make test-medium

# End-to-end tests (full system)
make test-large
```

## Troubleshooting

### Common Issues

#### 1. "Invalid authentication configuration" Error

**Cause**: `ROOT_VALIDATOR_KEY` environment variable is missing or empty.

**Solution**:
```bash
# Check environment variable
echo $ROOT_VALIDATOR_KEY

# Set in .env file
ROOT_VALIDATOR_KEY=sk_your_root_key_here
```

#### 2. "Invalid API key or insufficient permissions" Error

**Causes**:
- User API key is invalid or expired
- Root key lacks `api.*.verify_key` permission
- Network connectivity issues

**Debugging**:
```python
# Enable debug logging
import logging
logging.getLogger("wave_backend.auth").setLevel(logging.DEBUG)

# Check cache
from wave_backend.auth.unkey_client import get_unkey_client
client = get_unkey_client()
client.clear_cache()  # Clear cache and retry
```

#### 3. Cache Issues

**Symptoms**: Stale authentication results, permission changes not reflected

**Solution**:
```python
# Clear authentication cache
from wave_backend.auth.unkey_client import get_unkey_client
get_unkey_client().clear_cache()

# Or restart the application
```

#### 4. Network Timeouts

**Cause**: Unkey API connectivity issues or slow responses

**Configuration**:
```bash
# Increase timeout in .env
WAVE_AUTH_TIMEOUT=30.0

# Check network connectivity
curl -H "Authorization: Bearer $ROOT_VALIDATOR_KEY" \
     https://api.unkey.com/v2/keys.verifyKey
```

### Debug Information

Enable debug logging for authentication:

```python
import logging

# Configure logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("wave_backend.auth")
logger.setLevel(logging.DEBUG)
```

## Best Practices

### Security

1. **Key Management**:
   - Store `ROOT_VALIDATOR_KEY` securely (environment variables, secrets management)
   - Rotate keys regularly according to security policy
   - Never log or expose the root validation key

2. **Permission Design**:
   - Follow principle of least privilege
   - Use hierarchical roles appropriately
   - Regularly audit user permissions in Unkey workspace

3. **Network Security**:
   - Use HTTPS for all API communications
   - Implement proper timeout and retry logic
   - Monitor for unusual authentication patterns

### Performance

1. **Caching**:
   - Use default cache TTL (300 seconds) for most use cases
   - Clear cache when permissions change
   - Monitor cache hit rates for optimization

2. **API Usage**:
   - Batch user operations when possible
   - Implement circuit breakers for Unkey API calls
   - Use async/await patterns for concurrent requests

### Monitoring

1. **Metrics to Track**:
   - Authentication success/failure rates
   - API response times from Unkey
   - Cache hit/miss ratios
   - Role distribution across requests

2. **Alerting**:
   - High authentication failure rates
   - Unkey API unavailability
   - Unusual permission escalation attempts

### Development

1. **Environment Setup**:
   - Use separate Unkey workspaces for dev/staging/production
   - Implement proper key rotation procedures
   - Document role assignments and permissions

2. **Testing**:
   - Write tests for all authentication scenarios
   - Test network failure conditions
   - Validate role hierarchy enforcement

---

For additional support or questions about the authentication system, refer to the [API Usage Documentation](api-usage.md) or the inline documentation in the `wave_backend.auth` module.