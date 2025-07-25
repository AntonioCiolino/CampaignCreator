# Campaign Crafter API

## Overview

Campaign Crafter API is the backend server for CampaignCreator. It provides the core business logic, data persistence, and integration with Large Language Models (LLMs) for CampaignCreator applications, including the web UI (`campaign_crafter_ui`) and potentially other client applications.

## Key Features & Functional Areas

*   **Document Management**:
    *   `POST /documents/`: Create a new document.
    *   `GET /documents/`: List all documents.
    *   `GET /documents/{document_id}`: Retrieve a specific document.
    *   `PUT /documents/{document_id}`: Update a document.
    *   `DELETE /documents/{document_id}`: Delete a document.
*   **LLM Services**:
    *   `POST /llm/suggest/`: Get text suggestions from a configured LLM.
    *   `POST /llm/generate/`: Generate more extensive text content.
    *   `POST /images/generate`: Generate images using various models (DALL-E, Stable Diffusion, Gemini).
    *   (Further endpoints for specific LLM tasks may be added).
*   **(Planned) User Authentication & Management**:
    *   Endpoints for user registration, login, and profile management.
*   **(Planned) Project Management**:
    *   Endpoints for creating, organizing, and managing creative projects.

## Tech Stack

*   **Python**: Version 3.8+
*   **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints.
*   **SQLAlchemy**: SQL toolkit and Object-Relational Mapper (ORM) for database interaction.
*   **Pydantic**: Data validation and settings management using Python type annotations.
*   **Uvicorn**: ASGI server for running FastAPI applications.
*   **Poetry**: For dependency management and packaging (alternative to pip/requirements.txt, but instructions will cover `requirements.txt` for broader compatibility first).

## Prerequisites

To build and run this project locally, you will need:

*   **Python**: Version 3.8 or later.
    *   You can download it from [python.org](https://www.python.org/).
*   **pip**: Python package installer (usually comes with Python).
*   **(Optional) Git**: For cloning the repository.

## Getting Started

### 1. Clone the Repository

If you haven't already, clone the repository:
```bash
git clone <repository_url> # Replace <repository_url> with the actual repository URL
cd <path_to_campaign_crafter_api_directory> # Navigate to this project's directory
```

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

**On macOS and Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
You should see `(venv)` at the beginning of your command prompt.

### 3. Install Dependencies

Install the necessary Python packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```
*(Note: If a `poetry.lock` and `pyproject.toml` are present and you prefer Poetry, you can use `poetry install` instead, after installing Poetry itself.)*

### 4. Configure Environment Variables

The API requires certain environment variables for configuration, such as database connection strings and LLM API keys.

1.  **Copy the example environment file:**
    ```bash
    cp .env.example .env
    ```
    *(If `.env.example` does not exist, you will need to create a `.env` file manually based on the required variables mentioned below or in the application code.)*

2.  **Populate `.env` with your configurations:**
    Open the `.env` file in a text editor and fill in the required values. Key variables typically include:
    *   `DATABASE_URL`: The connection string for your database (e.g., `sqlite:///./campaign_crafter.db` for a local SQLite DB, or connection strings for PostgreSQL, MySQL, etc.).
    *   `OPENAI_API_KEY`: Your API key for OpenAI services (text and image generation).
    *   `GEMINI_API_KEY`: Your API key for Google Gemini services (text and image generation).
    *   `LLAMA_API_KEY`, `LLAMA_API_URL`: Configuration for Llama models.
    *   `DEEPSEEK_API_KEY`: Your API key for DeepSeek services.
    *   `OPENAI_DALLE_MODEL_NAME`, `OPENAI_DALLE_DEFAULT_IMAGE_SIZE`, `OPENAI_DALLE_DEFAULT_IMAGE_QUALITY`: Settings for DALL-E image generation.
    *   `LOCAL_LLM_PROVIDER_NAME`, `LOCAL_LLM_API_BASE_URL`, `LOCAL_LLM_DEFAULT_MODEL_ID`: Configuration for a generic local LLM provider.
    *   `PORT`: The port on which the application will listen. Defaults to `8000` if not set. This is particularly important for deployment platforms like Render, which may set this variable to route traffic correctly.
    *   `SECRET_KEY`: A secret key for signing JWTs or other security purposes. (Example, if you implement JWT)
    *   `ALGORITHM`: The algorithm used for JWT signing (e.g., `HS256`). (Example, if you implement JWT)
    *   `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiry time for access tokens. (Example, if you implement JWT)

    Refer to the `.env.example` file for a comprehensive list of all possible environment variables.

    **Example `.env` content (subset):**
    ```env
    DATABASE_URL="sqlite:///./test.db"
    OPENAI_API_KEY="your_openai_api_key_here"
    GEMINI_API_KEY="your_gemini_api_key_here"
    # ... other keys
    PORT=8000
    # ... other keys if using JWT
    ```

### 5. Database Migrations with Alembic

This project uses Alembic to manage database schema migrations. Alembic allows for versioning of your database schema, making it easier to evolve your database structure as your application changes.

**a. Configure Alembic:**

Ensure the `sqlalchemy.url` in your `alembic.ini` file matches the `DATABASE_URL` in your `.env` file. This is crucial for Alembic to connect to the correct database.

*   **`alembic.ini`:**
    ```ini
    [alembic]
    # ... other alembic configurations
    sqlalchemy.url = postgresql://user:password@host:port/dbname
    ```

*   **`.env`:**
    ```env
    DATABASE_URL="postgresql://user:password@host:port/dbname"
    ```

If you are using a different database system (e.g., SQLite for local development and PostgreSQL for production), you will need to update `sqlalchemy.url` in `alembic.ini` accordingly or manage different `alembic.ini` configurations for different environments. Often, the `env.py` script within your Alembic migration environment can be customized to read the `DATABASE_URL` from your environment variables (e.g., via `os.getenv('DATABASE_URL')`), making it more flexible.

**b. Generating a New Migration Script:**

To create a new, empty migration script, use the following command. You will then manually edit this script to define the schema changes.
```bash
alembic revision -m "create_some_table"
```
Replace `"create_some_table"` with a descriptive name for your migration (e.g., `"add_user_email_column"`).

**c. Auto-generating Migrations (Experimental - Review Carefully):**

Alembic can attempt to automatically generate a migration script based on the differences between your current database schema and your SQLAlchemy models.
```bash
alembic revision -m "add_new_column_to_user" --autogenerate
```
**Important:** Always review auto-generated migration scripts thoroughly. They might not always capture your intentions perfectly, especially with complex changes, new table creations, or type changes.

**d. Applying Migrations:**

To apply all pending migrations and bring the database to the latest version:
```bash
alembic upgrade head
```
You can also upgrade to a specific revision:
```bash
alembic upgrade <revision_id>
```

**e. Downgrading Migrations:**

To revert the last applied migration:
```bash
alembic downgrade -1
```
To downgrade to a specific revision:
```bash
alembic downgrade <revision_id>
```
Or to a specific relative number of revisions:
```bash
alembic downgrade -<number> # e.g., alembic downgrade -2
```

**f. Checking Current Migration Status:**

To see the current revision of the database and identify any pending migrations:
```bash
alembic current
```
To see the history of migrations:
```bash
alembic history
```

### 6. Running the Development Server

Once the dependencies are installed and the `.env` file is configured, you have a couple of ways to run the FastAPI application:

1.  **Via Programmatic Uvicorn (inside `app/main.py`):**
    ```bash
    python -m app.main
    ```
    This command executes the `if __name__ == "__main__":` block in `app/main.py`, which programmatically starts Uvicorn. This method is often suitable for production-like execution or when deploying with a process manager that expects your application to manage the server startup. It respects the `PORT` environment variable defined in your `.env` file.

2.  **Directly with Uvicorn CLI (for development):**
    ```bash
    python -m uvicorn app.main:app --reload
    ```
    This command is typically preferred for development because of the `--reload` flag, which automatically restarts the server when code changes are detected.
    *   `app.main:app`: Refers to the FastAPI application instance named `app` found in the `app/main.py` file.
    *   `--reload`: Enables auto-reloading.
    *   This method also respects the `PORT` environment variable if `app.main` is structured to read it when `app` is imported, or Uvicorn's `--port` option can be used explicitly (e.g., `uvicorn app.main:app --reload --port 8001`). By default, Uvicorn uses port 8000.

The server will typically be available on `http://127.0.0.1:8000` (or the port specified by the `PORT` environment variable if configured and respected by the chosen run method).

You can access the interactive API documentation (Swagger UI) at `http://<host>:<port>/docs` (e.g., `http://127.0.0.1:8000/docs`) and the alternative ReDoc documentation at `http://<host>:<port>/redoc`.

## Running Tests

This project uses `pytest` for running automated tests.

1.  **Ensure test dependencies are installed**:
    If test-specific dependencies are listed in a separate file (e.g., `requirements-dev.txt`) or as part of `pyproject.toml`'s dev group (for Poetry), make sure they are installed. Often, `pytest` itself is the main test dependency.
    ```bash
    pip install pytest httpx # httpx is useful for testing FastAPI endpoints
    ```

2.  **Run tests**:
    Navigate to the `campaign_crafter_api` directory (if not already there) and run:
    ```bash
    pytest
    ```
    Or, to be more explicit:
    ```bash
    python -m pytest
    ```
    Pytest will automatically discover and run tests from files named `test_*.py` or `*_test.py` in the current directory and its subdirectories. Test functions should be prefixed with `test_`.

### Running the MCP Server

This project includes a JSON-RPC server that acts as a passthrough to the main FastAPI application, conforming to the Model-Context-Protocol (MCP) specification. This allows clients like Claude Desktop to interact with the API.

1.  **Ensure Dependencies are Installed:**
    The MCP server requires `fastmcp`. Make sure it is in the `mcp_server/requirements.txt` and installed in your virtual environment.

2.  **Run the MCP Server:**
    From the root of the project directory, run the following command:
    ```bash
    python -m mcp_server.main_rpc
    ```
    By default, the server will start on `http://127.0.0.1:4000`.

    The MCP server will proxy requests to the FastAPI application, which should also be running. The `API_BASE_URL` environment variable in `main_rpc.py` controls the address of the FastAPI server (defaulting to `http://127.0.0.1:8000`).

### Writing Tests

*   Create test files in a `tests/` subdirectory (e.g., `tests/test_documents.py`) or alongside your app code if preferred (e.g., `test_main.py`).
*   Use FastAPI's `TestClient` (which uses `httpx`) for testing API endpoints.

**Example (in `tests/test_main.py`):**
```python
from fastapi.testclient import TestClient
from ..main import app # Adjust import based on your project structure

client = TestClient(app)

def test_read_main():
    response = client.get("/") # Assuming you have a root endpoint
    assert response.status_code == 200
    # Add more assertions based on your root endpoint's expected response
```

---

*This README provides a guide to setting up and running the Campaign Crafter API. As the project evolves, specific instructions or configurations might change. Ensure your `.env.example` and `requirements.txt` (or `pyproject.toml`) are up to date.*

## Feature Template Context Variables

When creating feature templates (via the Features UI or directly in `csv/features.csv`), the following context variables can be used. These are placeholders that the system will replace with actual data when a feature is invoked, primarily during section content regeneration via the `/api/campaigns/{campaign_id}/sections/{section_id}/regenerate` endpoint.

### General Context (Often available for most features)

*   `{campaign_title}`
    *   **Description**: The title of the current campaign.
    *   **Source**: Backend (`db_campaign.title`).
*   `{campaign_concept}`
    *   **Description**: The overall concept/summary of the current campaign.
    *   **Source**: Backend (`db_campaign.concept`).
*   `{section_title}`
    *   **Description**: The title of the current section being edited or generated.
    *   **Source**: Backend (derived from `db_section.title` or `section_input.new_title`).
*   `{section_type}`
    *   **Description**: The type of the current section (e.g., "NPC", "Location", "Generic").
    *   **Source**: Backend (derived from `db_section.type` or `section_input.section_type`).
*   `{existing_sections_summary}`
    *   **Description**: A summary of titles of other existing sections in the campaign (excluding the current one). Typically a semicolon-separated list.
    *   **Source**: Backend (generated by querying other sections).
*   `{campaign_characters}`
    *   **Description**: A summary or list of characters associated with the campaign. Typically a semicolon-separated list of names, possibly with brief descriptions.
    *   **Source**: Backend (generated by querying linked characters).

### Snippet-Specific Context (Primarily for features acting on highlighted text)

*   `{selected_text}`
    *   **Description**: The text currently highlighted by the user in the section editor. This is the primary input for most snippet features.
    *   **Source**: Frontend (`editorSelectionText` from Quill, passed in `context_data` within the regeneration payload).

### Full Section Generation Context

*   `{user_instructions}`
    *   **Description**: Any text present in the editor when a full section generation is triggered (if no specific text was highlighted for a snippet). This can be used as additional instructions or seed content for the master feature template.
    *   **Source**: Frontend (full editor content if no selection, passed in `context_data` within the regeneration payload).

### Type-Specific Context (Often derived from `{section_title}` by frontend for convenience)

These are often convenience variables passed by the frontend in `context_data` when a specific type of section is being worked on with a snippet feature, usually derived from `{section_title}`. The backend may not automatically populate these if not provided by the frontend.

*   `{npc_name}`
    *   **Description**: The name of an NPC, typically the `{section_title}` when `section_type` is "NPC".
    *   **Source**: Frontend (derived from `section.title`, passed in `context_data`).
*   `{location_name}`
    *   **Description**: The name of a location, typically the `{section_title}` when `section_type` is "Location".
    *   **Source**: Frontend (derived from `section.title`, passed in `context_data`).
*   `{quest_title}`
    *   **Description**: The title of a quest, typically the `{section_title}` when `section_type` is "Quest".
    *   **Source**: Frontend (derived from `section.title`, passed in `context_data`).

### Special System Feature Context (Used by non-section specific features)

*   `{user_prompt}`
    *   **Description**: The initial user prompt used to generate the entire campaign concept. (Used by the "Campaign" system feature).
    *   **Source**: Backend (`db_campaign.initial_user_prompt`).
*   `{count}`
    *   **Description**: A number, typically for requesting a certain quantity of items (e.g., for the "Campaign Names" system feature).
    *   **Source**: Passed in `context_data` or as a query parameter for specific system features.

**Note on Availability:**

Not all variables are available or relevant for every feature type or invocation method.
*   **Snippet Features** (invoked with a `feature_id` and typically acting on highlighted text) will always have `{selected_text}` if the frontend sends it. They can also access general context variables if their template includes them and the backend provides them.
*   **Full Section Features** (invoked by Type, without a `feature_id` in the payload) will have general context like `{campaign_concept}`, `{section_title}`, `{section_type}`, and potentially `{user_instructions}`. They typically do *not* use `{selected_text}`.
*   The backend regeneration endpoint (`/api/campaigns/{campaign_id}/sections/{section_id}/regenerate`) is responsible for assembling the final context available to the template. If a feature template includes a placeholder for which data cannot be reasonably provided in that specific scenario, the placeholder might remain unreplaced or be replaced with a default empty string/notice. It's crucial to check a feature's `required_context` when defining it.
