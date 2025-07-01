# TextEditorApp (Legacy iOS Application)

## Overview

`TextEditorApp` is an iOS application that was the original component of the CampaignCreator project. It was designed to provide local document editing capabilities with LLM-assisted content generation features directly on iOS devices.

Key features included:
*   Local document management (create, edit, save, load).
*   Direct integration with LLM providers (OpenAI GPT, Google Gemini) via user-provided API keys (managed in a `Secrets.swift` file).
*   Content import from various formats.
*   Content export, including a Homebrewery-compatible Markdown format.

## Current Status: Legacy

**This application is now considered a legacy component of the CampaignCreator suite and is no longer under active development or maintenance.**

The strategic focus of the CampaignCreator project has shifted entirely to the:
*   **`campaign_crafter_api`**: A robust backend API.
*   **`campaign_crafter_ui`**: A comprehensive web-based user interface.

These newer components provide a more flexible, scalable, and feature-rich platform.

## Purpose of this Codebase

The `TextEditorApp` codebase is retained primarily for:
*   Historical reference.
*   Access to any unique logic or features that might inform future development of the web platform, should the need arise.

## Setup (Historical)

If you were to attempt to build or run this project (not recommended for new development):
1.  Open `TextEditorApp.xcodeproj` in Xcode (Xcode 14.0 or later was previously recommended).
2.  The app targeted iOS 14.0.
3.  For LLM features to function, you would need to create a `Secrets.swift` file in `TextEditorApp/TextEditorApp/` with your API keys:
    ```swift
    // TextEditorApp/TextEditorApp/Secrets.swift
    import Foundation

    struct Secrets {
        static let openAIAPIKey = "YOUR_OPENAI_API_KEY"
        static let geminiAPIKey = "YOUR_GEMINI_API_KEY"
    }
    ```
4.  Dependencies (like ZipFoundation) were managed using Swift Package Manager in Xcode.

**Note:** There is no guarantee that the application will build or function correctly with current versions of Xcode, iOS, or third-party APIs, as it has not been maintained.

---

For current development and information, please refer to the main project README in the root directory.
