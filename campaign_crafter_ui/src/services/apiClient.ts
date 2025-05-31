import axios from 'axios';
import { getApiBaseUrl } from './env'; // Import the new function

const API_BASE_URL = getApiBaseUrl();

const apiClient = axios.create({
  baseURL: API_BASE_URL, // Use the centralized base URL
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
