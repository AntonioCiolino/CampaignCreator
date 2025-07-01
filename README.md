# CampaignCreator

## Project Overview

This repository hosts the "CampaignCreator" suite of tools, designed to assist creative writers, authors, and world-builders in crafting rich narratives and campaign settings.
The primary focus of current and future development is on:

*   **`campaign_crafter_api`**: A Python-based backend API using FastAPI. It handles LLM integrations (OpenAI, Gemini, local models), data persistence, user authentication, image generation, and core business logic for content creation and management.
*   **`campaign_crafter_ui`**: A React-based web interface that interacts with the `campaign_crafter_api` to provide a rich, web-based user experience for campaign editing, character management, and AI-assisted content generation.

The project originated with an iOS application, **`TextEditorApp`** (formerly CampaignCreator iOS App), which is now a secondary component with its development de-prioritized in favor of the more comprehensive API and Web UI.

### Root `requirements.txt` and `utils/`
The `requirements.txt` file and scripts within the `utils/` directory in the root of the repository are primarily for standalone utility scripts (e.g., data migration, content processing) or potentially an internal dashboard. These are generally not part of the main API (`campaign_crafter_api`) or UI (`campaign_crafter_ui`) application stacks but may support their development or maintenance.

## `TextEditorApp` (Formerly CampaignCreator iOS App)

The `TextEditorApp` (located in the `TextEditorApp/` directory) was the initial component of this project, offering local document editing and LLM-assisted content generation on iOS. While it remains a part of the ecosystem, its development is currently secondary to the API and web UI.

The iOS app features local document management and direct LLM integration (OpenAI GPT, Google Gemini) via API keys that would be configured in a `Secrets.swift` file (if used directly by the app). It also supports content import/export. Setup details are in the "Setup for Developers" section.

## `campaign_crafter_api` (Backend API)

### Purpose

The `campaign_crafter_api` is a Python-based backend service built with **FastAPI**. It is designed to:
*   Provide a centralized API for LLM interactions (OpenAI, Gemini, local/self-hosted models via an OpenAI-compatible interface).
*   Manage user accounts, authentication, and authorization.
*   Handle data storage for campaigns, characters, settings, and user-specific data.
*   Offer endpoints for AI-driven content generation (text, images), campaign structuring, and other features.
*   Support "Bring Your Own Key" (BYOK) for third-party LLM and image generation services.

### Tech Stack

*   **Python**: Core programming language.
*   **FastAPI**: Web framework for building the API.
*   **SQLAlchemy**: ORM for database interactions.
*   **Alembic**: For database migrations.
*   **pip & `requirements.txt`**: For dependency management (as per `campaign_crafter_api/requirements.txt`).
*   **Docker**: For containerization and deployment (setup available).

### Bring Your Own Key (BYOK) Support

The Campaign Creator API supports a "Bring Your Own Key" (BYOK) model for certain third-party services, enhancing user control and privacy. This applies to:

*   **OpenAI API Key**: For text generation (e.g., GPT models) and image generation (DALL-E).
*   **Google Gemini API Key**: For text generation and image generation with Gemini models.
*   **Stable Diffusion API Key**: For alternative image generation capabilities (e.g. via Stability AI).
*   Other LLM provider keys as supported.

**How it Works:**

*   **User-Provided Keys**: Users can securely submit their personal API keys for these services via their User Settings page in the web interface (`campaign_crafter_ui`). These keys are encrypted in storage.
*   **System Fallback for Superusers**: If a user is designated as a "superuser" and has not provided their own key for a specific service, the system may attempt to use a globally configured API key (set via environment variables like `OPENAI_API_KEY` or `STABLE_DIFFUSION_API_KEY`) for that superuser's requests. This is configurable.
*   **Feature Access**:
    *   If a user (who is not a superuser) has not provided their own API key for a service, features relying on that service will typically be disabled or limited for them.
    *   Superusers can generally access features using either their own key or the system's key if available.
    *   If a system key is not configured for a particular service, all users (including superusers) will need to provide their own key to access the corresponding features.

This system allows users to leverage their own API subscriptions and manage their usage directly, while still enabling administrators to provide system-level access for authorized superusers if desired.

### LLM Configuration for Content Generation

For features like auto-populating campaign sections, generating titles, or other AI-powered content creation, the Campaign Creator API needs to connect to a Large Language Model (LLM). Users must configure at least one LLM provider to enable these capabilities, either through their user settings (BYOK) or via system-level environment variables if they are superusers and system keys are provided.

Common environment variables read by the API on startup for system-level configuration include:

*   `OPENAI_API_KEY`: System's API key for accessing OpenAI models.
*   `GEMINI_API_KEY`: System's API key for accessing Google's Gemini models.
*   `DEEPSEEK_API_KEY`: System's API key for DeepSeek models.
*   `LOCAL_LLM_API_BASE_URL`: The base URL for a locally running LLM that exposes an OpenAI-compatible API (e.g., Ollama, LM Studio, Jan). Example: `http://localhost:11434/v1`.
    *   `LOCAL_LLM_DEFAULT_MODEL_ID`: Default model for the local LLM service (e.g., `ollama/llama2`).
    *   `LOCAL_LLM_PROVIDER_NAME`: Customizable identifier for the local provider.

If no LLM provider is configured (either by the user or the system), AI-driven content generation features will be limited or disabled. The user interface may guide users to configure a provider in their settings. Refer to `campaign_crafter_api/.env.example` for a comprehensive list of environment variables.

### Setup and Run

**Detailed setup and run instructions are in `campaign_crafter_api/README.md`.**
A typical quick start:
```bash
cd campaign_crafter_api
# Recommended: Create and activate a Python virtual environment
# python -m venv venv
# source venv/bin/activate (or .\venv\Scripts\activate on Windows)
pip install -r requirements.txt
# Copy .env.example to .env and configure your API keys and database settings
cp .env.example .env
# Run database migrations
alembic upgrade head
# To run the development server (with auto-reload):
python -m uvicorn app.main:app --reload
# Or, to run using the programmatic Uvicorn configuration in app/main.py:
# python -m app.main
```
Ensure Python is installed. API keys for LLM services should be configured in the `.env` file as per `campaign_crafter_api/.env.example`.

## `campaign_crafter_ui` (Web Interface)

### Purpose

The `campaign_crafter_ui` is a React-based web application providing a user interface for interacting with the `campaign_crafter_api`. Its goals include:
*   Offering a web-based editor for creating and managing campaigns, sections, characters, and other world-building elements.
*   Allowing users to manage their content and projects via a web browser.
*   Integrating with the backend API for LLM-powered suggestions, image generation, and other AI-assisted features.
*   Enabling users to manage their account settings, including submitting their own API keys (BYOK) for integrated services.

### Tech Stack

*   **TypeScript/JavaScript**: Core programming languages.
*   **React**: UI library for building the user interface.
*   **Create React App (react-scripts)**: For project setup, development server, and build scripts.
*   **React Router**: For client-side navigation.
*   **Axios**: For making HTTP requests to the backend API.
*   **React Context API** (and component state): For state management.

### Setup and Run

**Detailed setup and run instructions are in `campaign_crafter_ui/README.md`.**
A typical quick start:
```bash
cd campaign_crafter_ui
npm install # or yarn install
# Ensure the campaign_crafter_api is running and accessible
# Configure VITE_API_BASE_URL in campaign_crafter_ui/.env if necessary
npm run dev # or yarn dev
```
Ensure Node.js and npm (or yarn) are installed. The UI expects the `campaign_crafter_api` to be running and accessible.

## Project Status

*   **`campaign_crafter_api`**: Actively developed and operational. This Python (FastAPI)-based API is central to the project's functionality, providing LLM integration, data management, and user authentication.
*   **`campaign_crafter_ui`**: Actively developed and operational. This React-based web interface is the primary client for the `campaign_crafter_api`, offering a rich user experience for campaign creation and management.
*   **`TextEditorApp` (iOS App)**: Core local editing features were functional. Development is currently de-prioritized in favor of the API and web UI. The codebase serves as a reference but is not actively maintained.

## Setup for Developers

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd <repository_directory_name> # Replace <repository_directory_name> with your chosen directory name
    ```
2.  **Backend API (`campaign_crafter_api`)**:
    *   Navigate to `campaign_crafter_api/`.
    *   **Primary setup instructions are in `campaign_crafter_api/README.md`.** This includes Python virtual environment setup, installing dependencies from `requirements.txt`, configuring the `.env` file, and running database migrations.
3.  **Web UI (`campaign_crafter_ui`)**:
    *   Navigate to `campaign_crafter_ui/`.
    *   **Primary setup instructions are in `campaign_crafter_ui/README.md`.** This includes Node.js environment setup, installing dependencies with `npm` or `yarn`, and configuring environment variables (e.g., `VITE_API_BASE_URL`).
4.  **iOS App (`TextEditorApp`)** (Secondary Focus, Low Priority):
    *   Navigate to the `TextEditorApp/` directory (contains the Xcode project).
    *   Open the `TextEditorApp.xcodeproj` (or `.xcworkspace` if it exists) file in Xcode.
    *   This app is not actively maintained. Its primary value is as a reference for past features or concepts.
    *   If attempting to build, ensure you have a compatible Xcode version (e.g., Xcode 14.0 or later was previously recommended).
    *   **API Keys (iOS App)**: If you were to adapt its direct LLM features, you would need to manage API keys, potentially via a `Secrets.swift` file in `TextEditorApp/TextEditorApp/` as originally designed:
        ```swift
        // TextEditorApp/TextEditorApp/Secrets.swift
        import Foundation

        struct Secrets {
            static let openAIAPIKey = "YOUR_OPENAI_API_KEY" // Example
            static let geminiAPIKey = "YOUR_GEMINI_API_KEY" // Example
        }
        ```
    *   **Third-Party Libraries (iOS App)**: Dependencies like ZipFoundation were managed via Swift Package Manager.

## Future Goals (Overall Project)

*   **Enhanced Web Capabilities**: Continue to enrich the `campaign_crafter_ui` with advanced editing features, collaborative tools, and deeper integration with API functionalities.
*   **Expanded AI Features**: Introduce more sophisticated AI-driven tools for plot generation, character development, dialogue creation, and world consistency checking.
*   **Plugin/Module System**: Explore a plugin architecture for the API and UI to allow for community contributions and extensibility.
*   **Improved Import/Export**: Offer robust import/export options for various formats (e.g., Markdown, PDF, integration with other platforms like World Anvil), managed via the API.
*   **Advanced LLM Management**: Provide more granular control over LLM model selection, parameters, and context management through the UI.
*   **Performance and Scalability**: Continuously optimize the API and UI for performance and ensure the backend can scale to support a growing user base.
*   **Mobile Companion App (Conceptual)**: Revisit the possibility of a streamlined mobile companion app that syncs with the `campaign_crafter_api`, focusing on content review and light editing.
*   **Comprehensive Documentation**: Maintain and expand user and developer documentation for all components.
*   **Deployment & DevOps**: Refine Docker configurations, CI/CD pipelines, and explore scalable hosting solutions.

---

*This README provides a general guide. Specific build instructions, dependency versions, and configurations might evolve for each sub-project. Always refer to individual project READMEs (inside `campaign_crafter_api/` and `campaign_crafter_ui/`) for the most detailed and up-to-date information.*
