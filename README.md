# NarrateCraft - AI-Assisted Story & World Building iOS App

## Description

NarrateCraft is an iOS application designed for creative writers, authors, and world-builders. It serves as a document editor tailored for crafting stories, lore, and detailed world elements. The app integrates with multiple Large Language Models (LLMs) like OpenAI's GPT and Google's Gemini to provide text suggestions and assist in the creative process. Key goals include robust content import/export capabilities, with current support for Homebrewery and planned integration for World Anvil.

## Current Features

*   **iOS Native Text Editor**: Full-featured local document management including:
    *   Creating new text documents.
    *   Editing with a rich text view.
    *   Viewing and listing existing documents.
    *   Saving changes to local device storage.
    *   Loading documents for continued editing.
    *   Deleting documents.
    *   Renaming documents.
*   **Dual LLM Integration**:
    *   Supports text suggestions via API from OpenAI (GPT models) and Google Gemini.
    *   User interface (UISegmentedControl in the editor) to switch between selected LLM providers.
    *   API key management via a local `Secrets.swift` file.
*   **Content Import**:
    *   **JSON Files**: Import documents from structured JSON files (`[{ "title": "...", "content": "..." }]`).
    *   **Zip Archives**: Import documents from Zip archives containing `.txt` files and/or compatible JSON files. (Note: Relies on ZipFoundation, which is conceptually included).
    *   **Local Directories**: Recursively import `.txt` files from user-selected local directories.
*   **Homebrewery Export**:
    *   Generates Markdown output from the document content.
    *   Preserves user-defined markers such as `\page` (for page breaks) and `\column` (for column breaks) for easy copy-pasting into Homebrewery.
*   **Basic Theming**:
    *   A subtle, parchment-and-sepia inspired custom color palette.
    *   Custom fonts (Georgia, Helvetica Neue) for UI elements and editor.
    *   Use of SF Symbols for navigation bar icons.

## Project Status

Actively under development. Core editing features, dual LLM integration (OpenAI, Gemini), initial import (JSON, Zip, Directory), Homebrewery export, and basic theming are functional.

## Setup for Developers

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd <repository_directory> # Replace <repository_directory> with the cloned folder name
    ```
2.  **Open in Xcode**:
    *   Navigate to the `TextEditorApp` sub-directory.
    *   Open the `TextEditorApp.xcworkspace` file in Xcode. (Using `.xcworkspace` is important if the project has dependencies managed by CocoaPods or uses Swift Package Manager in a way that generates a workspace).
    *   Recommended: Xcode 14.0 or later (iOS 14.0 was targeted, so a compatible Xcode version is needed).
3.  **iOS Target**:
    *   The project currently targets iOS 14.0.
4.  **API Keys**:
    *   API keys for OpenAI and Google Gemini are required for the LLM suggestion features.
    *   Create a file named `Secrets.swift` inside the `TextEditorApp/TextEditorApp/` directory.
    *   This file is gitignored to protect your keys.
    *   Add your API keys to `Secrets.swift` with the following structure:

    ```swift
    // TextEditorApp/TextEditorApp/Secrets.swift
    import Foundation

    struct Secrets {
        static let openAIAPIKey = "YOUR_OPENAI_API_KEY" // Replace with your actual OpenAI key
        static let geminiAPIKey = "YOUR_GEMINI_API_KEY" // Replace with your actual Gemini key
    }
    ```
5.  **Third-Party Libraries**:
    *   **ZipFoundation**: This library is conceptually used for Zip archive import functionality. If building the project and this dependency is formally added, it would typically be managed via Swift Package Manager in Xcode:
        *   In Xcode: File > Add Packages...
        *   Enter the repository URL for ZipFoundation (e.g., `https://github.com/weichsel/ZipFoundation.git`).
        *   Follow the prompts to add the package to the `TextEditorApp` target.

## Future Goals (Briefly)

*   **World Anvil Export**: Direct integration for exporting content to World Anvil.
*   **Local LLM Support**: Explore options for on-device LLM integration for offline suggestions and enhanced privacy.
*   **Multi-User Collaboration**: Investigate real-time or asynchronous collaboration features.
*   **Advanced Editor Features**: Syntax highlighting for Markdown, richer text formatting options.

---

*This README provides a general guide. Specific build instructions or dependency versions might evolve.*
