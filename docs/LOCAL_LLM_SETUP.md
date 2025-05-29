# Local LLM Setup for Campaign Crafter

## 1. Introduction

Welcome to local Large Language Model (LLM) integration with Campaign Crafter! Using a local LLM offers several benefits:

-   **Privacy:** Your prompts and generated content stay on your machine.
-   **Offline Use:** Access LLMs without an internet connection (once models are downloaded).
-   **Open-Source Models:** Experiment with a wide variety of powerful open-source models.
-   **Customization & RAG:** Opens possibilities for future features like Retrieval Augmented Generation (RAG) using your own campaign documents.

This guide focuses on **Ollama** as the recommended local LLM server due to its ease of use and robust features. It will walk you through setting up Ollama and configuring the Campaign Crafter backend (`campaign_crafter_api`) to connect to it.

## 2. Prerequisites

-   **Ollama:** You'll need to download and install Ollama. System requirements and downloads can be found on the [official Ollama website](https://ollama.com).
-   **Campaign Crafter Backend:** This guide assumes you have the `campaign_crafter_api` backend code already cloned or set up on your system.

## 3. Setting up Ollama

### Step 3.1: Download and Install Ollama

1.  Go to the [Ollama download page](https://ollama.com/download).
2.  Download the version appropriate for your operating system:
    *   **macOS:** Download the `.zip` file and run the installer.
    *   **Windows (Preview):** Download and run the `.exe` installer.
    *   **Linux:** Use the provided `curl` script in your terminal:
        ```bash
        curl -fsSL https://ollama.com/install.sh | sh
        ```
3.  Follow the on-screen instructions provided by the Ollama installer or setup script.

### Step 3.2: Verify Ollama Installation

Once installed, Ollama typically runs as a background service. To verify it's running and accessible:

1.  Open your terminal (Command Prompt, PowerShell, or Terminal on macOS/Linux).
2.  Run the command:
    ```bash
    ollama --version
    ```
    This should output the Ollama version number.
3.  Alternatively, you can list any models you might have (it will be empty if it's a fresh install):
    ```bash
    ollama list
    ```
    This command also confirms the Ollama service is responsive.

### Step 3.3: Download a Model with Ollama

Ollama needs models to serve. You can pull models from the Ollama library. We recommend starting with a versatile and relatively resource-friendly model.

1.  **Choose a model.** Good starting points:
    *   `mistral:latest` (approx. 4.1GB, good balance of capability and resource use)
    *   `llama3:8b` (Meta's Llama 3 8B model, also excellent, approx. 4.7GB for q4_0)
    *   `gemma:2b` (Google's Gemma 2B model, smaller, approx. 1.4GB)

2.  **Pull the model.** Open your terminal and run (example uses `mistral`):
    ```bash
    ollama pull mistral:latest
    ```
    Replace `mistral:latest` with your chosen model if different (e.g., `ollama pull llama3:8b`). This will download the model; the time taken will depend on your internet speed.

3.  **Verify model download:**
    ```bash
    ollama list
    ```
    You should see the model you just pulled in the list.

### Step 3.4: Ensure Ollama Server is Running

-   After installation, Ollama usually starts automatically and runs as a background service.
-   The Ollama API server typically listens on `http://localhost:11434`.
-   If you suspect it's not running (e.g., commands like `ollama list` fail, or the backend can't connect), you might need to start it manually:
    *   **macOS/Linux:** Usually, it's managed by a system service. If you installed via the script, it should be running. You can try `ollama serve` if it seems down, but this is often not needed.
    *   **Windows:** The Ollama tray icon usually indicates if it's running.
    *   Refer to the [official Ollama documentation](https://github.com/ollama/ollama/blob/main/docs/linux.md) or your OS's service management for more details if needed.

## 4. Configuring Campaign Crafter Backend (`campaign_crafter_api`)

The Campaign Crafter backend needs to know where your local Ollama server is running.

### Step 4.1: Locate the `.env` File

1.  Navigate to the root directory of your `campaign_crafter_api` backend code.
2.  Look for a file named `.env`.
3.  If it doesn't exist, but a file named `.env.example` does, create a copy of `.env.example` and rename it to `.env`.
    ```bash
    # In your campaign_crafter_api directory
    cp .env.example .env
    ```

### Step 4.2: Edit the `.env` File

Open the `.env` file in a text editor and add or modify the following lines:

```dotenv
# --- Generic Local LLM Provider (OpenAI-Compatible API) ---
# This name is used as a key in the LLM factory to identify this service.
# You can choose a different name if you prefer, e.g., "ollama_local".
LOCAL_LLM_PROVIDER_NAME="ollama"

# This is the base URL for Ollama's OpenAI-compatible API endpoint.
LOCAL_LLM_API_BASE_URL="http://localhost:11434/v1"

# Set this to the ID of the model you pulled with Ollama (e.g., "mistral:latest", "llama3:8b").
# This will be the default model used if no specific model is requested for this provider.
LOCAL_LLM_DEFAULT_MODEL_ID="mistral:latest" 
# (Or replace "mistral:latest" with the model ID you pulled, e.g., "llama3:8b")
```

**Important Notes:**
-   Ensure `LOCAL_LLM_API_BASE_URL` is correct. If Ollama is running on the same machine as the backend, `http://localhost:11434/v1` is standard. If the backend is running in a Docker container and Ollama is on the host, you might need to use `http://host.docker.internal:11434/v1` (Docker Desktop) or the appropriate network IP.
-   The `LOCAL_LLM_DEFAULT_MODEL_ID` should be the model ID as Ollama knows it (e.g., what `ollama list` shows under the `NAME` column).

### Step 4.3: Restart the Backend

For the new `.env` settings to take effect, you must restart your `campaign_crafter_api` server.
-   If you're running it directly with `uvicorn main:app --reload`, stop it (Ctrl+C) and start it again.
-   If using Docker, restart the backend container.

## 5. Using Local LLMs in Campaign Crafter UI

Once your Ollama server is running with a downloaded model, and the `campaign_crafter_api` backend has been configured and restarted:

1.  Open the Campaign Crafter UI in your browser.
2.  Navigate to any feature that uses LLM generation (e.g., creating a new campaign concept, generating section content, or the "Generic Text Generator" tool if available).
3.  In the LLM model selection dropdown, you should now see your local provider and its models listed (e.g., "ollama/mistral:latest"). The name before the slash (`ollama/`) will match what you set for `LOCAL_LLM_PROVIDER_NAME` in the `.env` file.
4.  Select your local model and use the generation features as usual.

You can find more information about how the application indicates local LLM usage on the UI's **Settings** page (if available).

## 6. Basic Troubleshooting Tips

-   **"Local LLM Service Unavailable" or Connection Errors:**
    -   Ensure your Ollama server is running (try `ollama list` in terminal).
    -   Verify the `LOCAL_LLM_API_BASE_URL` in your backend's `.env` file is correct and accessible from where the backend is running. (e.g., `http://localhost:11434/v1`).
    -   Check for firewall issues if your backend and Ollama are on different machines or in different Docker networks.
-   **Model Not Found Errors (e.g., 404 for model operations):**
    -   Ensure the model ID specified in `LOCAL_LLM_DEFAULT_MODEL_ID` (in `.env`) or selected in the UI (e.g., "mistral:latest") exactly matches a model name shown by `ollama list`.
    -   Make sure you have pulled the model using `ollama pull model_name:tag`.
-   **Slow Performance:**
    -   Local LLMs can be resource-intensive. Check your system's RAM and CPU/GPU usage.
    -   Ensure Ollama is utilizing your GPU if available (this is usually automatic on supported hardware).
    -   Consider using smaller or more quantized models if performance is an issue on your hardware. Refer to the Ollama model library for different model sizes and quantization levels.

For more detailed Ollama troubleshooting, refer to the [official Ollama GitHub repository](https://github.com/ollama/ollama) and its documentation.

Enjoy using local LLMs with Campaign Crafter!
