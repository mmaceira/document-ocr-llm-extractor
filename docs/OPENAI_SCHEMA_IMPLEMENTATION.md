# OpenAI JSON Schema Implementation

## Implementation

Uses OpenAI structured outputs with two modes:
1. **JSON Schema Strict Mode** (preferred)
2. **JSON Object Mode** (fallback)

**Code location:** `core/extractor.py` → `extract_structured_data()`

**Flow:**
```python
# Get Pydantic schema
json_schema = model_class.model_json_schema()

# Transform for OpenAI strict mode
openai_schema = transform_schema(json_schema)

# Try strict mode, fallback to json_object
if SETTINGS.json_strict:
    try:
        response = client.chat.completions.create(
            response_format={"type": "json_schema", "json_schema": {...}}
        )
    except BadRequestError:
        response = client.chat.completions.create(
            response_format={"type": "json_object"}
        )
```

## Schema Transformation

OpenAI strict mode requires:
1. All properties in `required` array (even optional fields)
2. No `$defs` - must inline all references
3. Optional fields must allow `null` - use `["string", "null"]`

**Transformation steps:**
1. Inline `$defs` - replace `$ref` with actual schemas
2. Make all properties required
3. Make optional fields nullable: `"string"` → `["string", "null"]`
4. Apply to nested objects/arrays

**Example:**
```json
// Before
{"properties": {"categoria_gasto": {"type": "string"}}, "required": ["numero_deliverynote"]}

// After
{"properties": {"categoria_gasto": {"type": ["string", "null"]}}, "required": ["numero_deliverynote", "categoria_gasto"]}
```

## Error Handling

1. Try strict mode (if enabled)
2. On 400 error: fallback to `json_object` mode
3. On validation error: repair JSON (extract from markdown, unwrap nested)
4. After 3 attempts: raise error, save debug info to `debug_dir/llm_responses.json`

## Configuration

```bash
export DOCUMENT_LLM_JSON_STRICT=true   # Enable strict mode (default)
export DOCUMENT_LLM_JSON_STRICT=false  # Use json_object only
```
