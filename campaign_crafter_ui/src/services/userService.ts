import apiClient from './apiClient';

// Interface for User data (matching backend Pydantic User response model)
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  // Note: 'campaigns' and 'llm_configs' are not included here for now,
  // as they might not be needed for basic user management listings.
  // They can be added if a detailed user view requires them.
}

// Interface for creating a new user (matching backend UserCreate)
export interface UserCreatePayload {
  email: string;
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

// Create a new user
export const createUser = async (userData: UserCreatePayload): Promise<User> => {
  try {
    const response = await apiClient.post<User>('/api/v1/users/', userData);
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

// Update an existing user
export const updateUser = async (userId: number, userData: UserUpdatePayload): Promise<User> => {
  try {
    const response = await apiClient.put<User>(`/api/v1/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    console.error(`Error updating user with ID ${userId}:`, error);
    throw error;
  }
};

// Delete a user by ID
// The backend currently returns the deleted user object.
// If it were to return HTTP 204 No Content, this function signature would be Promise<void>.
export const deleteUser = async (userId: number): Promise<User> => {
  try {
    const response = await apiClient.delete<User>(`/api/v1/users/${userId}`);
    return response.data; // Assuming backend returns the deleted user
  } catch (error) {
    console.error(`Error deleting user with ID ${userId}:`, error);
    throw error;
  }
};
