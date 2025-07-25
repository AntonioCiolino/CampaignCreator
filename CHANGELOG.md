# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Numerous features and improvements to `campaign_crafter_api` and `campaign_crafter_ui` (details should be filled in from commit history before a new release).
- Full backend API with user authentication, CRUD operations for campaigns, characters, items, etc.
- Web UI for interacting with the API, including campaign editing, character management, AI content generation.
- BYOK support for OpenAI, Gemini, Stable Diffusion.
- Local LLM support.
- Image generation capabilities.

### Changed
- Project focus shifted significantly from the iOS app to the web API and UI.
- iOS app (`TextEditorApp`) is no longer under active development and is considered legacy.

### Removed
- (If any major features were removed, list them here)

## [0.1.0] - 2024-07-27 CampaignCreator Initial Release

### Added
- **Core Text Editing**:
    - Create, edit, view, save, load, delete, and rename text documents locally.
- **Dual LLM Integration**:
    - Text suggestions via API from OpenAI (GPT models) and Google Gemini.
    - UI (UISegmentedControl) in the editor to switch between LLM providers.
    - API key management via local `Secrets.swift`.
- **Content Import**:
    - Import documents from structured JSON files (`[{ "title": "...", "content": "..." }]`).
    - Import documents from Zip archives containing `.txt` files and/or compatible JSON files. (Conceptual support for ZipFoundation).
    - Recursively import `.txt` files from user-selected local directories.
- **Homebrewery Export**:
    - Generate Markdown output from document content.
    - Preserve user-defined markers (`\page`, `\column`) for Homebrewery.
    - Export view with "Copy to Clipboard" and "Share" options.
- **Basic Theming**:
    - Custom color palette (parchment, sepia, muted gold, teal navigation).
    - Custom fonts (Georgia for headings/editor, Helvetica Neue for body).
    - Use of SF Symbols for navigation bar icons.
- **Documentation**:
    - Initial `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `LICENSE` files for CampaignCreator.
