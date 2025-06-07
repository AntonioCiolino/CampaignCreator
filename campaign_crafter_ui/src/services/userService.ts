import apiClient from './apiClient';
import { User as AppUser } from '../types/userTypes'; // Use AppUser to avoid conflict or rename local

// Interface for User data - This should align with AppUser from userTypes.ts
// For now, functions like getUsers might return this local User type.
// Ideally, all user service functions should consistently return AppUser.
export interface User { // Local User type, potentially to be deprecated/aligned
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  disabled: boolean;
  is_superuser: boolean;
  // is_active field is deprecated in favor of disabled
}

// Interface for creating a new user (matching backend UserCreate)
// Backend UserCreate: username, password, email (optional), full_name (optional), is_superuser (optional)
export interface UserCreatePayload {
  username: string; // Added username
  email?: string | null; // Made email optional
  password: string;
  full_name?: string | null;
  // is_active?: boolean; // Field removed from backend UserCreate model
  is_superuser?: boolean;
}

// Interface for updating an existing user (matching backend UserUpdate)
// Backend UserUpdate: inherits UserBase (username, email, full_name) + password, disabled, is_superuser
export interface UserUpdatePayload {
  username?: string; // Added username
  email?: string | null; // Made email optional
  password?: string;
  full_name?: string | null;
  // is_active?: boolean; // Field removed, use disabled
  disabled?: boolean; // Added disabled
  is_superuser?: boolean;
}

// Fetch all users (with optional pagination) - Should return AppUser[]
export const getUsers = async (skip: number = 0, limit: number = 100): Promise<AppUser[]> => {
  try {
    const response = await apiClient.get<AppUser[]>('/users/', { // Assuming /users/ path, needs /api/v1 if not in base
      params: { skip, limit },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};

// Fetch a single user by ID - Should return AppUser
export const getUserById = async (userId: number): Promise<AppUser> => {
  try {
    const response = await apiClient.get<AppUser>(`/users/${userId}`); // Assuming /users/ path
    return response.data;
  } catch (error) {
    console.error(`Error fetching user with ID ${userId}:`, error);
    throw error;
  }
};
  password: string; // Corrected to string
  full_name?: string | null;
  is_active?: boolean;
  is_superuser?: boolean;
}

// Interface for updating an existing user (matching backend UserUpdate)
export interface UserUpdatePayload {
  email?: string;
  password?: string; // For providing a new password
  full_name?: string | null;
  is_active?: boolean;
  is_superuser?: boolean;
}

// Fetch all users (with optional pagination)
export const getUsers = async (skip: number = 0, limit: number = 100): Promise<User[]> => {
  try {
    const response = await apiClient.get<User[]>('/api/v1/users/', {
      params: { skip, limit },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error; // Re-throw to be handled by the calling component
  }
};

// Fetch a single user by ID
export const getUserById = async (userId: number): Promise<User> => {
  try {
    const response = await apiClient.get<User>(`/api/v1/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching user with ID ${userId}:`, error);
    throw error;
  }
};

// --- Auth related functions ---

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const loginUser = async (username_or_email: string, password: string): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', username_or_email);
  formData.append('password', password);

  const response = await apiClient.post<TokenResponse>('/auth/token', formData, { // API path for token
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

// Fetch current user details
export const getMe = async (): Promise<AppUser> => {
  const response = await apiClient.get<AppUser>('/users/me'); // API path for /me
  return response.data;
};

// Create a new user - Should return AppUser
export const createUser = async (userData: UserCreatePayload): Promise<AppUser> => {
  try {
    const response = await apiClient.post<AppUser>('/users/', userData); // Assuming /users/ path
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

// Update an existing user - Should return AppUser
export const updateUser = async (userId: number, userData: UserUpdatePayload): Promise<AppUser> => {
  try {
    const response = await apiClient.put<AppUser>(`/users/${userId}`, userData); // Assuming /users/ path
    return response.data;
  } catch (error) {
    console.error(`Error updating user with ID ${userId}:`, error);
    throw error;
  }
};

// Delete a user by ID - Should return AppUser
export const deleteUser = async (userId: number): Promise<AppUser> => {
  try {
    const response = await apiClient.delete<AppUser>(`/users/${userId}`); // Assuming /users/ path
    return response.data;
  } catch (error) {
    console.error(`Error deleting user with ID ${userId}:`, error);
    throw error;
  }
};
