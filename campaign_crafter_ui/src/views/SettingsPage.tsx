import React, { useState, useEffect } from 'react';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import './SettingsPage.css';

// Placeholder for fetching actual configured provider name from backend (if such endpoint existed)
// For now, we'll assume the default or let user know it's backend-configured.
const BACKEND_CONFIGURED_LOCAL_PROVIDER_NAME = "local_llm"; // Example

const SettingsPage: React.FC = () => {
  // State for a hypothetical frontend-configurable URL (for future or if design changes)
  // For this task, we are primarily informing about backend configuration.
  const [localLlmApiBaseUrlInput, setLocalLlmApiBaseUrlInput] = useState<string>('');
  const [saveStatus, setSaveStatus] = useState<string>('');

  // Effect to load a user-set URL from localStorage if it were implemented for frontend direct use
  useEffect(() => {
    const storedUrl = localStorage.getItem('userLocalLlmApiBaseUrl');
    if (storedUrl) {
      setLocalLlmApiBaseUrlInput(storedUrl);
    }
  }, []);

  const handleSaveLocalLlmUrl = () => {
    // This functionality is illustrative for now, as the primary local LLM URL
    // is configured on the backend. If frontend needed to store a user-override
    // or an alternative local URL for some direct client-side LLM calls (not current architecture),
    // this is where it would be saved.
    // localStorage.setItem('userLocalLlmApiBaseUrl', localLlmApiBaseUrlInput);
    setSaveStatus(`Illustrative save: URL "${localLlmApiBaseUrlInput}" would be saved to localStorage if used by frontend.`);
    setTimeout(() => setSaveStatus(''), 3000);
  };

  return (
    <div className="settings-page-wrapper container">
      <h2 className="settings-page-title">Application Settings</h2>

      <section className="settings-section">
        <h3>Local Large Language Model (LLM) Configuration</h3>
        <p>
          This application can connect to a locally running LLM server (like Ollama, LM Studio, or a llama.cpp server)
          that provides an OpenAI-compatible API endpoint.
        </p>
        <p>
          <strong>To enable local LLM support, the backend API must be configured.</strong> This typically involves setting
          the following environment variables in the backend's <code>.env</code> file:
        </p>
        <ul>
          <li><code>LOCAL_LLM_API_BASE_URL</code>: The base URL of your local LLM server's OpenAI-compatible API 
            (e.g., <code>http://localhost:11434/v1</code> for Ollama, or the URL provided by LM Studio).</li>
          <li><code>LOCAL_LLM_PROVIDER_NAME</code>: (Optional) A name for this provider, defaults to "<code>local_llm</code>" if not set. This name will prefix models from your local server in selection dropdowns.</li>
          <li><code>LOCAL_LLM_DEFAULT_MODEL_ID</code>: (Optional) The default model ID your local server should use if no specific model is requested by the application (e.g., "<code>mistral:latest</code>").</li>
        </ul>
        <p>
          Once the backend is configured and restarted, and your local LLM server is running, models served by it
          should automatically appear in the LLM selection dropdowns throughout this application, prefixed with the
          configured provider name (e.g., "<code>{BACKEND_CONFIGURED_LOCAL_PROVIDER_NAME}/your_model_name</code>").
        </p>
        
        <Card className="settings-note">
            <p>
                <strong>Note:</strong> The input field below is for future features or testing specific client-side connections.
                Currently, the primary connection to your local LLM is managed by the backend configuration described above.
            </p>
        </Card>

        <div className="settings-input-group" style={{marginTop: '1.5rem'}}>
          <Input
            id="localLlmApiBaseUrl"
            name="localLlmApiBaseUrl"
            label="Local LLM API Base URL (Informational / Future Use):"
            type="text"
            value={localLlmApiBaseUrlInput}
            onChange={(e) => setLocalLlmApiBaseUrlInput(e.target.value)}
            placeholder="e.g., http://localhost:11434/v1"
            // disabled // Could be disabled to emphasize it's informational for current backend setup
          />
           <Button 
            onClick={handleSaveLocalLlmUrl} 
            variant="secondary" 
            size="sm"
            style={{marginTop: '0.5rem'}}
            // disabled // Could be disabled
           >
            Save to Browser (Illustrative)
          </Button>
          {saveStatus && <p style={{color: 'green', fontSize: '0.9em', marginTop: '0.5rem'}}>{saveStatus}</p>}
        </div>
      </section>

      {/* Future sections for other settings can be added here */}
      {/* 
      <section className="settings-section">
        <h3>Other Frontend Settings</h3>
        <p>Placeholder for other application-specific frontend settings.</p>
      </section>
      */}
    </div>
  );
};

export default SettingsPage;

// To make this view accessible, you would typically add a route in your main App router,
// for example, in src/routes/AppRoutes.tsx:
//
// import SettingsPage from '../views/SettingsPage';
//
// <Route path="/settings" element={<SettingsPage />} />
//
// And provide a NavLink or button in the main layout (e.g., in Layout.tsx's header or a sidebar).
