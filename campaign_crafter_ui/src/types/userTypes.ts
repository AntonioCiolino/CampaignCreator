export interface User {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  disabled: boolean;
  is_superuser: boolean;
}

// This file can also contain other user-related types if needed in the future,
// e.g., UserCreate, UserUpdate if they differ significantly from backend
// or if you want frontend-specific variations.
// For now, just the main User model for responses.
