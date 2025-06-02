# CampaignCreator

## Project Overview

This repository contains the "CampaignCreator" suite of tools, designed to assist creative writers, authors, and world-builders. The "CampaignCreator" project includes:

*   **CampaignCreator (iOS App)**: The original iOS application for document editing and LLM-assisted content generation. (See section below for more details).
*   **campaign_crafter_api**: A Python-based backend API that provides LLM integrations, data management, and other services for the CampaignCreator ecosystem. This is a core focus for future development.
*   **campaign_crafter_ui**: A React-based web interface that will interact with the `campaign_crafter_api` to offer a web-based experience for some of the CampaignCreator functionalities.

## CampaignCreator (iOS App)

The CampaignCreator iOS application was the original project under this name, providing a document editor for story crafting with LLM assistance. While it remains part of the ecosystem, the broader "CampaignCreator" project is now expanding to focus more on the backend API (`campaign_crafter_api`) and web interface (`campaign_crafter_ui`).

The iOS app offers local document management and direct integration with LLMs (OpenAI GPT, Google Gemini) via API keys configured in a local `Secrets.swift` file. It also includes features for content import (JSON, Zip, local directories) and Homebrewery export.

For setup, see the "Setup for Developers" section. Future development of the iOS app will be coordinated with the overall project direction, which prioritizes the API and web components.

## campaign_crafter_api (Backend API)

### Purpose

The `campaign_crafter_api` is a Python-based backend service built with Flask. It is designed to:
*   Provide a centralized API for LLM interactions (OpenAI, Gemini, and potentially others).
*   Manage user accounts and authentication (planned).
*   Handle data storage and synchronization for web-based features (planned).
*   Offer endpoints for features that are better suited for server-side implementation.

### Tech Stack

*   **Python**: Core programming language.
*   **Flask**: Web framework for building the API.
*   **Poetry**: For dependency management and packaging.
*   **(Planned) Docker**: For containerization and deployment.

### Setup and Run

Detailed setup and run instructions can be found in `campaign_crafter_api/README.md`.
A quick start is typically:
```bash
cd campaign_crafter_api
poetry install
poetry run flask run
```
Ensure you have Python and Poetry installed. API keys for LLM services need to be configured as per the API's specific instructions (usually via environment variables or a `.env` file).

## campaign_crafter_ui (Web Interface)

### Purpose

The `campaign_crafter_ui` is a React-based web application that will provide a user interface for interacting with the `campaign_crafter_api`. Its goals include:
*   Offering a web-based editor for story and world-building.
*   Allowing users to manage their content and projects via a web browser.
*   Integrating with the backend API for LLM suggestions and other features.

### Tech Stack

*   **JavaScript/TypeScript**: Core programming languages.
*   **React**: UI library for building the user interface.
*   **Vite**: Frontend build tool.
*   **(Planned) Redux/Zustand**: For state management.

### Setup and Run

Detailed setup and run instructions can be found in `campaign_crafter_ui/README.md`.
A quick start is typically:
```bash
cd campaign_crafter_ui
npm install # or yarn install
npm run dev # or yarn dev
```
Ensure you have Node.js and npm (or yarn) installed.

## Project Status

*   **CampaignCreator (iOS App)**: Core local editing features, direct LLM integration, import/export, and basic theming are functional. Future development will be aligned with the broader project goals, which prioritize the API and web UI.
*   **campaign_crafter_api**: Under active development. This Python-based API is central to the project's strategy, providing LLM integration and backend services.
*   **campaign_crafter_ui**: Under active development. This React-based web interface will be the primary client for the `campaign_crafter_api`.

## Setup for Developers

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd <repository_directory_name> # Replace <repository_directory_name> with your chosen directory name
    ```
2.  **iOS App (CampaignCreator)**:
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
3.  **Backend API (campaign_crafter_api)**:
    *   Navigate to `campaign_crafter_api/`. See its `README.md` for detailed setup (requires Python and Poetry).
4.  **Web UI (campaign_crafter_ui)**:
    *   Navigate to `campaign_crafter_ui/`. See its `README.md` for detailed setup (requires Node.js and npm/yarn).

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
