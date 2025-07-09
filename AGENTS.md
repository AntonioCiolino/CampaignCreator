# AGENTS.md

This file provides guidelines and instructions for AI agents working on this project.

## General Principles

*   **Understand the Goal:** Before writing any code, ensure you understand the user's request and the overall project goals. Ask for clarification if anything is unclear.
*   **Plan Your Work:** Create a clear plan of action before making changes. Use the `set_plan` tool to outline your steps.
*   **Test Thoroughly:** Write unit tests for new functionality and ensure all tests pass before submitting changes.
*   **Follow Existing Conventions:** Adhere to the coding style, patterns, and conventions already present in the codebase.
*   **Be Autonomous:** Strive to solve problems independently. Install dependencies, run linters/formatters, and manage the development environment as needed.
*   **Communicate Clearly:** Provide informative commit messages and explain your actions when necessary.

## Project-Specific Guidelines

*   **Primary Focus**: Development efforts are concentrated on `campaign_crafter_api` (FastAPI backend), `campaign_crafter_ui` (React frontend), and the `CampaignCreatorApp` (iOS application).
*   **API Development (`campaign_crafter_api`)**:
    *   Follow FastAPI best practices.
    *   Ensure new endpoints are documented (e.g., OpenAPI schema).
    *   Write unit and integration tests for new services and endpoints. Tests are typically run using `pytest`.
    *   Manage dependencies with `pip` and `requirements.txt`.
    *   Database migrations are handled by Alembic. Create new migration scripts for schema changes.
    *   Refer to `campaign_crafter_api/README.md` for detailed setup and contribution guidelines.
*   **UI Development (`campaign_crafter_ui`)**:
    *   The project is set up using **Create React App** (`react-scripts`).
    *   Develop components using React and TypeScript.
    *   State management is handled via **React Context API** and component-level state.
    *   Navigation is managed by **React Router**.
    *   API communication is done using **Axios**.
    *   Style components using CSS modules or a consistent styling approach (e.g., as seen in `App.css`, `*.css` files per component).
    *   Write component and integration tests (e.g., using Jest/React Testing Library, as configured by Create React App).
    *   Manage dependencies with `npm` or `yarn` and `package.json`.
    *   Refer to `campaign_crafter_ui/README.md` for detailed setup and contribution guidelines.
*   **AI-Assisted Development**: This project has significantly benefited from AI-assisted development (e.g., using tools like GitHub Copilot, Aider, or similar agents like yourself, Jules).
    *   When AI-generated code is used, ensure it is reviewed, understood, and tested thoroughly.
    *   Credit AI assistance appropriately if company/project policy dictates.
    *   Be mindful of potential biases or inefficiencies in AI-generated code and refactor as needed.
    *   Focus on using AI to accelerate development, not replace critical thinking and design.

## Working with Me (the User)

*   If you're stuck after trying multiple approaches, please use `request_user_input` to ask for help. Provide context on what you've tried.
*   If a request is ambiguous, use `request_user_input` for clarification.
*   If you need to make a decision that significantly alters the scope of the original request, or involves architectural changes, please discuss it with me first using `request_user_input`.
*   When you have completed a task or a significant part of it, use `submit` with a descriptive branch name (e.g., `feat/new-feature`, `fix/bug-fix`, `docs/update-readme`) and a conventional commit message.
*   Feel free to suggest improvements or alternative approaches if you think they are beneficial, especially if they improve code quality, performance, or maintainability.

## Code Style

*   **Python (`campaign_crafter_api`)**: Follow PEP 8. Use a formatter like Black and a linter like Flake8 if configured in the project.
*   **TypeScript/JavaScript (`campaign_crafter_ui`)**: Follow common community best practices. Use Prettier for code formatting if configured. Adhere to ESLint rules if present.
*   Aim for clarity, readability, and maintainability in all code.

## Dependencies

*   **`campaign_crafter_api`**: Managed via `pip` and `campaign_crafter_api/requirements.txt`. Update this file when adding or changing dependencies.
*   **`campaign_crafter_ui`**: Managed via `npm` (or `yarn`) and `campaign_crafter_ui/package.json`. Use `npm install --save <package>` or `yarn add <package>` to add dependencies.
*   **Root `requirements.txt`**: For utility scripts. Update as needed if modifying these scripts.

## Testing

*   **`campaign_crafter_api`**:
    *   Tests are located in `campaign_crafter_api/app/tests/`.
    *   Run tests using `pytest` from the `campaign_crafter_api` directory.
    *   Ensure new code is covered by tests.
*   **`campaign_crafter_ui`**:
    *   Tests are co-located with components or in `src/__tests__` or similar.
    *   Run tests using `npm test` or `yarn test` from the `campaign_crafter_ui` directory.
    *   Ensure new components and logic are tested.

This document is a living guide. Please update it as necessary to reflect best practices and project evolution, especially if new tools, conventions, or AI agent capabilities are introduced.
