# ADR-001: LLM Configuration Architecture

**Status:** Accepted (with known technical debt)  
**Date:** 2026-01-28  
**Authors:** Development Team

## Context

The Campaign Crafter API needs to support multiple LLM providers (OpenAI, Anthropic, Google, xAI, etc.) while allowing users to bring their own API keys. The current implementation has evolved organically and has several architectural issues that need to be documented for future refactoring.

## Current Architecture

### Two-Table Design

1. **`llm_configs` table** - Registry of available LLM models
   - Defines which models exist and how to connect to them
   - Contains: `id`, `provider`, `model_name`, `display_name`, `api_key_env_var`, `is_active`
   - The `api_key_env_var` column specifies which environment variable to use as fallback

2. **`users` table** - Stores user-specific API keys
   - Columns: `openai_api_key`, `sd_api_key`, `gemini_api_key`, `other_llm_api_key`
   - Keys are encrypted at rest
   - Boolean flags track if keys are provided: `openai_api_key_provided`, etc.

### API Key Resolution Priority

When making an LLM call, the system resolves API keys in this order:
1. User's stored key (from `users` table) - if they entered one in Settings
2. Environment variable (from server's `.env`) - fallback if user hasn't set one

### Data Flow

```
User Settings UI → PUT /api/v1/users/me/keys → users table (encrypted)
                                                    ↓
LLM Service ← llm_configs (model registry) ← selected_llm_id
     ↓
Resolve API key: user.openai_api_key || env.OPENAI_API_KEY
     ↓
Make API call to provider
```

## Problems with Current Design

### 1. No Automatic Seeding of `llm_configs`

**Issue:** The `llm_configs` table is not seeded on application startup. When deploying to a new database (e.g., Supabase), the table is empty and no LLM models are available.

**Impact:** Users cannot select any LLM models until an admin manually inserts records via SQL.

**Current Workaround:** Manual SQL insertion:
```sql
INSERT INTO llm_configs (id, provider, model_name, display_name, api_key_env_var, is_active, created_at, updated_at)
VALUES ('openai/gpt-4o-mini', 'openai', 'gpt-4o-mini', 'GPT-4o Mini', 'OPENAI_API_KEY', true, NOW(), NOW());
```

### 2. Hardcoded API Key Columns on Users Table

**Issue:** The `users` table has fixed columns for specific providers:
- `openai_api_key`
- `sd_api_key` 
- `gemini_api_key`
- `other_llm_api_key`

**Impact:** 
- Adding a new provider (e.g., xAI, Anthropic, Perplexity) requires a database migration
- "Other LLM" is a catch-all that doesn't scale
- No way to store multiple keys for the same provider type

### 3. UI Only Shows 4 Key Slots

**Issue:** `UserSettingsPage.tsx` has hardcoded inputs for only 4 API key types, matching the database columns.

**Impact:** Users cannot configure keys for newer providers like xAI Grok, Anthropic Claude, DeepSeek, etc.

### 4. Disconnect Between `llm_configs.api_key_env_var` and User Keys

**Issue:** The `api_key_env_var` in `llm_configs` (e.g., `XAI_API_KEY`) doesn't map to any column in the `users` table.

**Impact:** For providers beyond the 4 hardcoded ones, there's no way for users to provide their own keys - only server-level env vars work.

### 5. No Admin UI for Managing `llm_configs`

**Issue:** There's no UI to add, edit, or disable LLM configurations.

**Impact:** All model registry changes require direct database access.

## Recommended Future Refactoring

### Phase 1: Add LLM Config Seeding (Quick Win)

Add to `app/core/seeding.py`:
```python
def seed_llm_configs(db: Session):
    """Seed default LLM configurations if table is empty."""
    existing = db.query(LLMConfig).first()
    if existing:
        return
    
    default_configs = [
        LLMConfig(id="openai/gpt-4o-mini", provider="openai", ...),
        # ... more configs
    ]
    db.add_all(default_configs)
    db.commit()
```

### Phase 2: Flexible User API Keys (Medium Effort)

Replace hardcoded columns with a separate `user_api_keys` table:

```sql
CREATE TABLE user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'xai', etc.
    api_key_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
```

Benefits:
- Add new providers without migrations
- Users can have keys for any provider
- Clean separation of concerns

### Phase 3: Admin UI for LLM Configs (Larger Effort)

Create admin endpoints and UI to:
- List all LLM configs
- Add new models
- Enable/disable models
- Set default models per provider

### Phase 4: Dynamic Settings UI (Larger Effort)

Update `UserSettingsPage.tsx` to:
- Fetch available providers from `llm_configs`
- Dynamically render API key inputs based on unique providers
- Support adding keys for any provider in the registry

## SQL Seed Script (Current Workaround)

Until Phase 1 is implemented, use this SQL to seed a new database:

```sql
INSERT INTO llm_configs (id, provider, model_name, display_name, api_key_env_var, is_active, created_at, updated_at)
VALUES 
  -- OpenAI
  ('openai/gpt-4o', 'openai', 'gpt-4o', 'GPT-4o', 'OPENAI_API_KEY', true, NOW(), NOW()),
  ('openai/gpt-4o-mini', 'openai', 'gpt-4o-mini', 'GPT-4o Mini', 'OPENAI_API_KEY', true, NOW(), NOW()),
  -- ... (see full script in project documentation)
  
  -- xAI Grok
  ('xai/grok-3', 'xai', 'grok-3', 'Grok 3', 'XAI_API_KEY', true, NOW(), NOW()),
  ('xai/grok-3-fast', 'xai', 'grok-3-fast', 'Grok 3 Fast', 'XAI_API_KEY', true, NOW(), NOW()),
  
  -- Anthropic Claude
  ('anthropic/claude-3-5-sonnet', 'anthropic', 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 'ANTHROPIC_API_KEY', true, NOW(), NOW()),
  
  -- Google Gemini
  ('gemini/gemini-2.0-flash', 'gemini', 'gemini-2.0-flash', 'Gemini 2.0 Flash', 'GOOGLE_API_KEY', true, NOW(), NOW()),
  
  -- DeepSeek
  ('deepseek/deepseek-reasoner', 'deepseek', 'deepseek-reasoner', 'DeepSeek Reasoner (R1)', 'DEEPSEEK_API_KEY', true, NOW(), NOW());
```

## Decision

Accept the current architecture with documented technical debt. Prioritize:
1. **Immediate:** Document the manual seeding process (this ADR)
2. **Short-term:** Implement Phase 1 (auto-seeding)
3. **Medium-term:** Implement Phase 2 (flexible user keys)
4. **Long-term:** Phases 3-4 as needed

## Consequences

### Positive
- Clear documentation of current state
- Roadmap for incremental improvement
- Manual workaround available for new deployments

### Negative
- New deployments require manual SQL intervention
- Users limited to 4 API key types in UI
- Adding new providers requires code changes

## Related Files

- `app/core/seeding.py` - Current seeding logic (missing LLM configs)
- `app/orm_models.py` - LLMConfig and User models
- `campaign_crafter_ui/src/pages/UserSettingsPage.tsx` - API keys UI
- `campaign_crafter_ui/src/services/userService.ts` - API key update service
- `app/services/llm_factory.py` - LLM service factory
