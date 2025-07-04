// src/services/featureService.ts
import apiClient from './apiClient';
import { Feature, FeatureCreate, FeatureUpdate } from '../types/featureTypes';
import axios from 'axios'; // Import axios to use isAxiosError

const API_BASE_URL = '/api/v1/features'; // Matches backend router prefix

export const getFeatures = async (): Promise<Feature[]> => {
  const response = await apiClient.get<Feature[]>(`${API_BASE_URL}/`);
  return response.data;
};

export const getFeature = async (id: number): Promise<Feature> => {
  const response = await apiClient.get<Feature>(`${API_BASE_URL}/${id}`);
  return response.data;
};

export const createFeature = async (featureData: FeatureCreate): Promise<Feature> => {
  try {
    const response = await apiClient.post<Feature>(`${API_BASE_URL}/`, featureData);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    } else if (error instanceof Error) {
      throw new Error(error.message);
    }
    throw new Error('An unknown error occurred while creating the feature.');
  }
};

export const updateFeature = async (id: number, featureData: FeatureUpdate): Promise<Feature> => {
  try {
    const response = await apiClient.put<Feature>(`${API_BASE_URL}/${id}`, featureData);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    } else if (error instanceof Error) {
      throw new Error(error.message);
    }
    throw new Error('An unknown error occurred while updating the feature.');
  }
};

export const deleteFeature = async (id: number): Promise<void> => {
  try {
    await apiClient.delete<void>(`${API_BASE_URL}/${id}`);
  } catch (error) {
    if (axios.isAxiosError(error) && error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    } else if (error instanceof Error) {
      throw new Error(error.message);
    }
    throw new Error('An unknown error occurred while deleting the feature.');
  }
};
