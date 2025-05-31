// src/services/env.ts
export const getApiBaseUrl = (): string => {
  const baseUrl = import.meta.env?.VITE_API_BASE_URL; // Optional chaining for env
  if (baseUrl) {
    return baseUrl;
  }
  // Fallback if running in a context where Vite env vars aren't available as expected,
  // or if the variable is not set.
  console.warn('VITE_API_BASE_URL not found in import.meta.env, defaulting to http://localhost:8000. Ensure .env file is set up correctly for Vite for other environments.');
  return 'http://localhost:8000'; // Changed default
};
