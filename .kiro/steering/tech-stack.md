# Campaign Crafter API - Technology Stack

## Backend (campaign_crafter_api)

- **Framework**: FastAPI
- **Python**: 3.8+
- **ORM**: SQLAlchemy (sync, not async)
- **Database**: SQLite (dev) / PostgreSQL (prod) - must write DB-agnostic code
- **Migrations**: Alembic
- **Validation**: Pydantic V2 (use `.model_dump()`, `.model_validate()`)
- **Auth**: JWT via python-jose, passlib for password hashing
- **Settings**: pydantic-settings with `.env` files

## LLM Integrations

Services in `app/services/`:
- `openai_service.py` - OpenAI GPT + DALL-E
- `gemini_service.py` - Google Gemini
- `llama_service.py` - Llama models
- `deepseek_service.py` - DeepSeek
- `local_llm_service.py` - Generic OpenAI-compatible local LLMs
- `llm_factory.py` - Factory pattern for LLM service selection

## Image Generation

- OpenAI DALL-E
- Stable Diffusion (Stability AI)
- Google Gemini
- Azure Blob Storage for image persistence

## Key Dependencies

```
fastapi, uvicorn, sqlalchemy, pydantic, pydantic-settings
python-jose[cryptography], passlib[bcrypt]
openai, google-generativeai
azure-storage-blob, azure-identity
alembic, pytest, httpx
```

## Running the API

```bash
cd campaign_crafter_api
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8001
```

## Running Tests

```bash
cd campaign_crafter_api
source venv/bin/activate
pytest
```
