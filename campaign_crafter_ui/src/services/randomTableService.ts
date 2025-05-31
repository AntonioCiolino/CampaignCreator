// Defines the structure of the response from the /api/random-tables endpoint
export interface TableNameListResponse {
  table_names: string[];
}

// Defines the structure of the response from the /api/random-tables/{table_name}/item endpoint
export interface RandomItemResponse {
  table_name: string;
  item: string | null; // Item can be null if table is empty or other server-side logic allows
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Fetches the list of all available random table names from the backend.
 * @returns A promise that resolves to an array of table name strings.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export const getAllRandomTableNames = async (): Promise<string[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/random-tables`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Network response was not ok.' }));
      throw new Error(errorData.detail || `Failed to fetch random table names: ${response.statusText}`);
    }
    const data: TableNameListResponse = await response.json();
    if (!data.table_names) {
        console.warn('No table_names found in response:', data);
        return [];
    }
    return data.table_names;
  } catch (error) {
    console.error("Error fetching all random table names:", error);
    throw error;
  }
};

/**
 * Fetches a random item from a specified table from the backend.
 * @param tableName The name of the table to retrieve an item from.
 * @returns A promise that resolves to a RandomItemResponse object.
 * @throws Will throw an error if the network request fails (excluding 404) or the API returns an unexpected error.
 *         If the table is not found (404), the promise will be rejected with an error.
 */
export const getRandomItemFromTable = async (tableName: string): Promise<RandomItemResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/random-tables/${tableName}/item`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `Failed to fetch item from table '${tableName}'.` }));
      // Specific message for 404, more generic for others
      const errorMessage = response.status === 404
        ? `Random table '${tableName}' not found.`
        : (errorData.detail || `Failed to fetch item from table '${tableName}': ${response.statusText}`);
      throw new Error(errorMessage);
    }
    const data: RandomItemResponse = await response.json();
    return data;
  } catch (error) {
    // Log the error before re-throwing, so it's visible in the console.
    // Avoid logging "Random table not found" as a severe error if it's a common case handled by callers.
    if (error instanceof Error && error.message.includes("not found")) {
         console.warn(error.message); // Log 404s as warnings
    } else {
        console.error(`Error fetching random item from table '${tableName}':`, error);
    }
    throw error; // Re-throw the error to be handled by the caller
  }
};
