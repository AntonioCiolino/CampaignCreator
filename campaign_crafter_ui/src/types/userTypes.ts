export interface User {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  disabled: boolean;
  is_superuser: boolean;
  openai_api_key_provided?: boolean;
  sd_api_key_provided?: boolean;
  sd_engine_preference?: string;
  gemini_api_key_provided?: boolean;
  other_llm_api_key_provided?: boolean;
  avatar_url?: string | null; // New field for avatar URL
  description?: string | null;
  appearance?: string | null;
}

export interface UserApiKeysPayload {
  openai_api_key?: string;
  sd_api_key?: string;
  gemini_api_key?: string;
  other_llm_api_key?: string;
}

// This file can also contain other user-related types if needed in the future,
// e.g., UserCreate, UserUpdate if they differ significantly from backend
// or if you want frontend-specific variations.
// For now, just the main User model for responses.
