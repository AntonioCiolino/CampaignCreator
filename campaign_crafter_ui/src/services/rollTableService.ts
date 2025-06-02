// src/services/rollTableService.ts
import apiClient from './apiClient';
import { RollTable, RollTableCreate, RollTableUpdate } from '../types/rollTableTypes';

const API_BASE_URL = '/api/v1/roll_tables'; // Matches backend router prefix

export const getRollTables = async (): Promise<RollTable[]> => {
  const response = await apiClient.get<RollTable[]>(`${API_BASE_URL}/`);
  return response.data;
};

export const getRollTable = async (id: number): Promise<RollTable> => {
  const response = await apiClient.get<RollTable>(`${API_BASE_URL}/${id}`);
  return response.data;
};

export const createRollTable = async (rollTableData: RollTableCreate): Promise<RollTable> => {
  const response = await apiClient.post<RollTable>(`${API_BASE_URL}/`, rollTableData);
  return response.data;
};

export const updateRollTable = async (id: number, rollTableData: RollTableUpdate): Promise<RollTable> => {
  const response = await apiClient.put<RollTable>(`${API_BASE_URL}/${id}`, rollTableData);
  return response.data;
};

export const deleteRollTable = async (id: number): Promise<void> => {
  await apiClient.delete<void>(`${API_BASE_URL}/${id}`);
};
