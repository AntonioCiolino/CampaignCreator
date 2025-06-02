# Campaign Crafter UI

## Overview

Campaign Crafter UI is the frontend web application for CampaignCreator. It serves as the primary user interface for interacting with the services provided by the `campaign_crafter_api`. This application aims to provide a web-based experience for creative writers, authors, and world-builders, and aims to be the primary interface for the CampaignCreator suite.

## Key Features (Planned & In Development)

*   **Web-Based Text Editor**: A rich text editor for creating and managing story documents, lore, and world-building notes online.
*   **Project and Document Management**: Organize creative projects, documents, and related elements.
*   **LLM Integration**: Access AI-assisted text suggestions and content generation by connecting to the `campaign_crafter_api`.
*   **User Authentication**: Secure user accounts and project access (dependent on API implementation).
*   **Content Synchronization**: (Future Goal) Synchronize content across different client platforms via the backend API.

## Tech Stack

*   **React**: A JavaScript library for building user interfaces.
*   **Vite**: A fast frontend build tool that provides a quicker and leaner development experience compared to Create React App.
*   **TypeScript**: A superset of JavaScript that adds static typing for more robust code.
*   **JavaScript (ES6+)**: Core programming language.
*   **CSS / SASS**: For styling the application.
*   **(Planned) State Management**: Redux, Zustand, or React Context API for managing application state.
*   **(Planned) Testing**: Jest, React Testing Library for unit and integration tests.

## Prerequisites

To build and run this project locally, you will need:

*   **Node.js**: Version 18.x or later recommended. (Includes npm)
    *   You can download it from [nodejs.org](https://nodejs.org/).
*   **npm** (Node Package Manager) or **yarn**:
    *   npm is included with Node.js.
    *   yarn can be installed via npm: `npm install --global yarn`.

## Getting Started

### 1. Clone the Repository

If you haven't already, clone the repository:
```bash
git clone <repository_url> # Replace <repository_url> with the actual repository URL
cd <path_to_campaign_crafter_ui_directory> # Navigate to this project's directory
```

### 2. Install Dependencies

Install the necessary Node.js packages using either npm or yarn:

Using npm:
```bash
npm install
```

Or using yarn:
```bash
yarn install
```

### 3. Configure Environment Variables (if applicable)

If the application requires specific environment variables (e.g., the URL for `campaign_crafter_api`), create a `.env` file in the `campaign_crafter_ui` root directory.

Example `.env` file:
```
VITE_API_BASE_URL=http://localhost:5000/api
```
*(Note: The actual environment variables needed will depend on the API integration.)*

### 4. Running the Development Server

To start the Vite development server:

Using npm:
```bash
npm run dev
```

Or using yarn:
```bash
yarn dev
```
This will typically start the application on `http://localhost:5173` (Vite's default) or another port if specified in `vite.config.js`. The page will automatically reload if you make edits to the source code.

## Connecting to the Backend API (`campaign_crafter_api`)

The Campaign Crafter UI is designed to communicate with the `campaign_crafter_api` to:

*   Fetch user data, documents, and project information.
*   Send requests for creating, updating, or deleting content.
*   Submit prompts to LLMs and receive generated text suggestions.

This communication is typically done using HTTP requests (e.g., via the `fetch` API or a library like `axios`) to the endpoints exposed by the backend API. The base URL for the API will be configured (likely via an environment variable as shown above) to allow the UI to connect to the API running locally or in a deployed environment.

## Building for Production

To create an optimized production build:

Using npm:
```bash
npm run build
```

Or using yarn:
```bash
yarn build
```
This command will generate a `dist` folder containing the static assets for your application, ready for deployment to a web server or hosting platform.

## Linting and Formatting

(Assuming ESLint and Prettier are or will be set up)
To lint your code:
```bash
npm run lint
```
To format your code:
```bash
npm run format
```

---

*This README provides a guide to setting up and running the Campaign Crafter UI. As the project evolves, specific instructions or configurations might change.*
