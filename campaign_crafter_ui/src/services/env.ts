// src/services/env.ts
export const getApiBaseUrl = (): string => {
  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  if (baseUrl) {
    return baseUrl;
  }
  // Fallback if running in a context where Vite env vars aren't available as expected,
  // or if the variable is not set.
  console.warn('REACT_APP_API_BASE_URL not found in process.env, defaulting to http://localhost:8000. Ensure .env file is set up correctly.');
  return 'http://localhost:8000'; // Changed default
};
