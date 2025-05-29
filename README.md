# CampaignCreator Monorepo

## Project Overview

This repository is a monorepo for the "CampaignCreator" suite of tools, designed to assist creative writers, authors, and world-builders. The name "CampaignCreator" is used as an umbrella term for the entire project, which currently includes:

*   **CampaignCreator (iOS App)**: An iOS application for document editing, story crafting, and LLM-assisted content generation. This was the original project and retains the main name.
*   **campaign_crafter_api**: A Python-based backend API that provides LLM integrations and other services for the CampaignCreator ecosystem.
*   **campaign_crafter_ui**: A React-based web interface that will interact with the `campaign_crafter_api` to offer a web-based experience for some of the CampaignCreator functionalities.

## CampaignCreator (iOS App)

### Description

The CampaignCreator iOS application is a document editor tailored for crafting stories, lore, and detailed world elements. It integrates with multiple Large Language Models (LLMs) like OpenAI's GPT and Google's Gemini to provide text suggestions and assist in the creative process. Key goals include robust content import/export capabilities, with current support for Homebrewery and planned integration for World Anvil.

### Current Features (iOS App)

*   **iOS Native Text Editor**: Full-featured local document management including:
    *   Creating new text documents.
    *   Editing with a rich text view.
    *   Viewing and listing existing documents.
    *   Saving changes to local device storage.
    *   Loading documents for continued editing.
    *   Deleting documents.
    *   Renaming documents.
*   **Dual LLM Integration (via local `Secrets.swift`)**:
    *   Supports text suggestions via API from OpenAI (GPT models) and Google Gemini.
    *   User interface (UISegmentedControl in the editor) to switch between selected LLM providers.
    *   API key management via a local `Secrets.swift` file (specific to the iOS app).
*   **Content Import (iOS App)**:
    *   **JSON Files**: Import documents from structured JSON files (`[{ "title": "...", "content": "..." }]`).
    *   **Zip Archives**: Import documents from Zip archives containing `.txt` files and/or compatible JSON files. (Note: Relies on ZipFoundation, which is conceptually included).
    *   **Local Directories**: Recursively import `.txt` files from user-selected local directories.
*   **Homebrewery Export (iOS App)**:
    *   Generates Markdown output from the document content.
    *   Preserves user-defined markers such as `\page` (for page breaks) and `\column` (for column breaks) for easy copy-pasting into Homebrewery.
*   **Basic Theming (iOS App)**:
    *   A subtle, parchment-and-sepia inspired custom color palette.
    *   Custom fonts (Georgia, Helvetica Neue) for UI elements and editor.
    *   Use of SF Symbols for navigation bar icons.

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

*   **CampaignCreator (iOS App)**: Actively under development. Core editing features, local LLM integration, initial import/export, and basic theming are functional.
*   **campaign_crafter_api**: Initial development phase. Basic Flask app setup with Poetry. LLM routing and core endpoints are being defined.
*   **campaign_crafter_ui**: Initial development phase. Basic React app setup with Vite. Component structure and API integration are being planned.

## Setup for Developers (Monorepo)

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd campaign_creator_monorepo # Or your chosen directory name
    ```
2.  **iOS App (CampaignCreator)**:
    *   Navigate to the `CampaignCreator` sub-directory.
    *   Open the `CampaignCreator.xcworkspace` file in Xcode. (Using `.xcworkspace` is important).
    *   Recommended: Xcode 14.0 or later.
    *   **iOS Target**: Currently targets iOS 14.0.
    *   **API Keys (iOS App)**: For LLM features in the iOS app, create `Secrets.swift` in `CampaignCreator/CampaignCreator/` with your OpenAI and Gemini keys:
        ```swift
        // CampaignCreator/CampaignCreator/Secrets.swift
        import Foundation

        struct Secrets {
            static let openAIAPIKey = "YOUR_OPENAI_API_KEY"
            static let geminiAPIKey = "YOUR_GEMINI_API_KEY"
        }
        ```
    *   **Third-Party Libraries (iOS App)**:
        *   **ZipFoundation**: Conceptually used. If formally adding, use Swift Package Manager in Xcode.
3.  **Backend API (campaign_crafter_api)**:
    *   See `campaign_crafter_api/README.md` for detailed setup. Requires Python and Poetry.
4.  **Web UI (campaign_crafter_ui)**:
    *   See `campaign_crafter_ui/README.md` for detailed setup. Requires Node.js and npm/yarn.

## Future Goals (Overall Project)

*   **Full Feature Parity (where applicable)**: Bring relevant iOS app features to the web UI via the API.
*   **Cross-Platform Synchronization**: Allow users to work on their projects across iOS and web.
*   **World Anvil Export/Import**: Robust integration for both import and export with World Anvil.
*   **Local LLM Support**: Explore options for on-device LLM integration (iOS) and self-hosted LLMs (via API) for enhanced privacy and offline capabilities.
*   **Multi-User Collaboration**: Investigate real-time or asynchronous collaboration features across platforms.
*   **Advanced Editor Features**: Syntax highlighting for Markdown, richer text formatting options (iOS and Web).
*   **Comprehensive API Services**: Expand the `campaign_crafter_api` to support a wider range of functionalities.
*   **Deployment & Scalability**:
    *   Containerize the API and UI for easier deployment (e.g., using Docker).
    *   Explore scalable hosting solutions.

---

*This README provides a general guide. Specific build instructions or dependency versions might evolve for each sub-project. Refer to individual project READMEs for more detailed information.*
