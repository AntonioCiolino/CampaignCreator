export interface User {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  disabled: boolean;
  is_superuser: boolean;
  // Add these new fields
  openai_api_key_provided?: boolean;
  sd_api_key_provided?: boolean;
  gemini_api_key_provided?: boolean; // Added for Gemini API key status
  sd_engine_preference?: string;
}

// This file can also contain other user-related types if needed in the future,
// e.g., UserCreate, UserUpdate if they differ significantly from backend
// or if you want frontend-specific variations.
// For now, just the main User model for responses.
