import apiClient from './apiClient';
import { User as AppUser } from '../types/userTypes';

// Remove local User interface, use AppUser from userTypes.ts exclusively.

// Interface for creating a new user (matching backend UserCreate)
// Backend UserCreate: username, password, email (optional), full_name (optional), is_superuser (optional)
export interface UserCreatePayload {
  username: string;
  email?: string | null;
  password: string;
  full_name?: string | null;
  is_superuser?: boolean;
}

// Interface for updating an existing user (matching backend UserUpdate)
// Backend UserUpdate: inherits UserBase (username, email, full_name) + password, disabled, is_superuser
export interface UserUpdatePayload {
  username?: string;
  email?: string | null | undefined; // Allow undefined to skip update, null to clear (if API supports)
  password?: string;
  full_name?: string | null | undefined;
  disabled?: boolean;
  is_superuser?: boolean;
  sd_engine_preference?: string;
}

// Fetch all users (with optional pagination) - Returns AppUser[]
export const getUsers = async (skip: number = 0, limit: number = 100): Promise<AppUser[]> => {
  try {
    const response = await apiClient.get<AppUser[]>('/api/v1/users/', {
      params: { skip, limit },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};

// Upload user avatar
export const uploadUserAvatar = async (formData: FormData): Promise<AppUser> => {
  try {
    const response = await apiClient.post<AppUser>('/api/v1/users/me/avatar', formData, {
      headers: {
        // Content-Type is not set by Axios for FormData, browser will set it with boundary
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading user avatar:', error);
    throw error;
  }
};

// Interface for updating user API keys
export interface UserApiKeysPayload {
  openai_api_key?: string | null; // Allow null to clear
  sd_api_key?: string | null;     // Allow null to clear
  gemini_api_key?: string | null;
  other_llm_api_key?: string | null;
}

// Update current user's API keys
export const updateUserApiKeys = async (payload: UserApiKeysPayload): Promise<AppUser> => {
  try {
    const response = await apiClient.put<AppUser>('/api/v1/users/me/keys', payload);
    return response.data;
  } catch (error) {
    console.error('Error updating user API keys:', error);
    throw error;
  }
};

// Fetch a single user by ID - Returns AppUser
export const getUserById = async (userId: number): Promise<AppUser> => {
  try {
    const response = await apiClient.get<AppUser>(`/api/v1/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching user with ID ${userId}:`, error);
    throw error;
  }
};

// --- Auth related functions ---
// (Keep existing TokenResponse, loginUser, getMe as they are correct)

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const loginUser = async (username_or_email: string, password: string): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', username_or_email);
  formData.append('password', password);

  const response = await apiClient.post<TokenResponse>('/api/v1/auth/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

// Fetch current user details
export const getMe = async (): Promise<AppUser> => {
  const response = await apiClient.get<AppUser>('/api/v1/users/me');
  return response.data;
};

// Create a new user - Should return AppUser
export const createUser = async (userData: UserCreatePayload): Promise<AppUser> => {
  try {
    const response = await apiClient.post<AppUser>('/api/v1/users/', userData);
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

// Update an existing user - Should return AppUser
export const updateUser = async (userId: number, userData: UserUpdatePayload): Promise<AppUser> => {
  try {
    const response = await apiClient.put<AppUser>(`/api/v1/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    console.error(`Error updating user with ID ${userId}:`, error);
    throw error;
  }
};

// Delete a user by ID - Should return AppUser
export const deleteUser = async (userId: number): Promise<AppUser> => {
  try {
    const response = await apiClient.delete<AppUser>(`/api/v1/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting user with ID ${userId}:`, error);
    throw error;
  }
};
