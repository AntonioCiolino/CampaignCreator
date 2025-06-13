# CampaignCreator

## Project Overview

This repository hosts the "CampaignCreator" suite of tools, designed to assist creative writers, authors, and world-builders.
The primary focus of current and future development is on:

*   **`campaign_crafter_api`**: A Python-based backend API using FastAPI. It handles LLM integrations, data persistence, and core business logic.
*   **`campaign_crafter_ui`**: A React-based web interface that interacts with the `campaign_crafter_api` to provide a rich, web-based user experience.

The project originated with an iOS application, **CampaignCreator (iOS App)**, which is now a secondary component with its development de-prioritized in favor of the API and Web UI.

### Root `requirements.txt`
The `requirements.txt` file in the root directory contains dependencies for separate utility scripts or an internal dashboard (e.g., using Streamlit, Pandas). These are not part of the main API (`campaign_crafter_api`) or UI (`campaign_crafter_ui`) application stacks.

## CampaignCreator (iOS App)

The CampaignCreator iOS application was the initial component of this project, offering local document editing and LLM-assisted content generation. While it remains a part of the ecosystem, its development is currently secondary to the API and web UI.

The iOS app features local document management and direct LLM integration (OpenAI GPT, Google Gemini) via API keys in a `Secrets.swift` file. It also supports content import/export. Setup details are in the "Setup for Developers" section.

## campaign_crafter_api (Backend API)

### Purpose

The `campaign_crafter_api` is a Python-based backend service built with **FastAPI**. It is designed to:
*   Provide a centralized API for LLM interactions (OpenAI, Gemini, and potentially others).
*   Manage user accounts and authentication (planned).
*   Handle data storage and synchronization for web-based features (planned).
*   Offer endpoints for features that are better suited for server-side implementation.

### Tech Stack

*   **Python**: Core programming language.
*   **FastAPI**: Web framework for building the API.
*   **pip & `requirements.txt`**: For dependency management (as per `campaign_crafter_api/README.md`).
*   **(Planned) Docker**: For containerization and deployment.

### Bring Your Own Key (BYOK) Support

The Campaign Creator API now supports a "Bring Your Own Key" (BYOK) model for certain third-party services, enhancing user control and privacy. Currently, this applies to:

*   **OpenAI API Key**: Used for text generation (e.g., GPT models) and image generation (DALL-E).
*   **Stable Diffusion API Key**: Used for alternative image generation capabilities.

**How it Works:**

*   **User-Provided Keys**: Users can securely submit their personal API keys for these services via their User Settings page in the web interface (`campaign_crafter_ui`). These keys are encrypted in storage.
*   **System Fallback for Superusers**: If a user is designated as a "superuser" and has not provided their own key for a specific service, the system will attempt to use a globally configured API key (set via environment variables like `OPENAI_API_KEY` or `STABLE_DIFFUSION_API_KEY`) for that superuser's requests.
*   **Feature Access**:
    *   If a user (who is not a superuser) has not provided their own API key for a service, features relying on that service will be disabled for them.
    *   Superusers can access features using either their own key or the system's key.
    *   If a system key is not configured, even superusers will need to provide their own key to access the corresponding features.

This system allows users to leverage their own API subscriptions and manage their usage directly, while still enabling administrators to provide system-level access for authorized superusers.

### Setup and Run

**Detailed setup and run instructions are in `campaign_crafter_api/README.md`.**
A quick start is typically:
```bash
cd campaign_crafter_api
pip install -r requirements.txt
# To run the development server (with auto-reload):
python -m uvicorn app.main:app --reload
# Or, to run using the programmatic Uvicorn configuration in app/main.py:
# python -m app.main
```
Ensure you have Python installed. API keys for LLM services need to be configured as per the API's specific instructions (usually via a `.env` file).

## campaign_crafter_ui (Web Interface)

### Purpose

The `campaign_crafter_ui` is a React-based web application that will provide a user interface for interacting with the `campaign_crafter_api`. Its goals include:
*   Offering a web-based editor for story and world-building.
*   Allowing users to manage their content and projects via a web browser.
*   Integrating with the backend API for LLM suggestions and other features.
*   Allowing users to manage their account settings, including submitting their own API keys for integrated services (OpenAI, Stable Diffusion).

### Tech Stack

*   **JavaScript/TypeScript**: Core programming languages.
*   **React**: UI library for building the user interface.
*   **Vite**: Frontend build tool.
*   **(Planned) Redux/Zustand**: For state management.

### Setup and Run

**Detailed setup and run instructions are in `campaign_crafter_ui/README.md`.**
A quick start is typically:
```bash
cd campaign_crafter_ui
npm install # or yarn install
npm run dev # or yarn dev
```
Ensure you have Node.js and npm (or yarn) installed.

## Project Status

*   **`campaign_crafter_api`**: Under active development. This Python (FastAPI)-based API is central to the project's strategy.
*   **`campaign_crafter_ui`**: Under active development. This React-based web interface is the primary client for the `campaign_crafter_api`.
*   **CampaignCreator (iOS App)**: Core local editing features are functional. Future development is de-prioritized in favor of the API and web UI.

## Setup for Developers

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd <repository_directory_name> # Replace <repository_directory_name> with your chosen directory name
    ```
2.  **Backend API (`campaign_crafter_api`)**:
    *   Navigate to `campaign_crafter_api/`.
    *   **Primary setup instructions are in `campaign_crafter_api/README.md`.** This includes Python environment setup and installing dependencies from `requirements.txt`.
3.  **Web UI (`campaign_crafter_ui`)**:
    *   Navigate to `campaign_crafter_ui/`.
    *   **Primary setup instructions are in `campaign_crafter_ui/README.md`.** This includes Node.js environment setup and installing dependencies with `npm` or `yarn`.
4.  **iOS App (CampaignCreator)** (Secondary Focus):
    *   Navigate to the `CampaignCreator` directory (contains the Xcode project).
    *   Open the `CampaignCreator.xcworkspace` file in Xcode.
    *   Recommended: Xcode 14.0 or later.
    *   **iOS Target**: Currently targets iOS 14.0.
    *   **API Keys (iOS App)**: For LLM features, create `Secrets.swift` in `CampaignCreator/CampaignCreator/` (this is specific to the iOS app's direct LLM access):
        ```swift
        // CampaignCreator/CampaignCreator/Secrets.swift
        import Foundation

        struct Secrets {
            static let openAIAPIKey = "YOUR_OPENAI_API_KEY"
            static let geminiAPIKey = "YOUR_GEMINI_API_KEY"
        }
        ```
    *   **Third-Party Libraries (iOS App)**:
        *   **ZipFoundation**: Used for some import features. If formally adding or updating, use Swift Package Manager in Xcode.


## Future Goals (Overall Project)

*   **Expansion of Web Capabilities**: Prioritize bringing rich features to the web UI, leveraging the `campaign_crafter_api`. This includes adapting relevant concepts from the original iOS application.
*   **Data Synchronization**: Enable users to access and manage their projects across different platforms (e.g., web and potentially mobile applications) through the central API.
*   **World Anvil Export/Import**: Robust integration for both import and export with World Anvil, likely managed via the API and available to connected clients.
*   **Flexible LLM Support**: Continue to support LLM integration via the API, exploring options for self-hosted models. On-device LLM capabilities for any client applications (like the existing iOS app) will be considered based on platform feasibility and project priorities.
*   **Multi-User Collaboration**: Investigate real-time or asynchronous collaboration features, primarily focused on the web platform.
*   **Advanced Editor Features**: Implement syntax highlighting for Markdown and richer text formatting options, with a primary focus on the web UI.
*   **Comprehensive API Services**: Expand the `campaign_crafter_api` to support a wider range of functionalities.
*   **Deployment & Scalability**:
    *   Containerize the API and UI for easier deployment (e.g., using Docker).
    *   Explore scalable hosting solutions.

---

*This README provides a general guide. Specific build instructions or dependency versions might evolve for each sub-project. Refer to individual project READMEs for more detailed information.*
