// src/types/rollTableTypes.ts
export interface RollTableItem {
  id: number;
  min_roll: number;
  max_roll: number;
  description: string;
  roll_table_id: number; // Matches Pydantic model
}

export interface RollTableItemCreate {
  min_roll: number;
  max_roll: number;
  description: string;
}

// RollTableItemUpdate could be defined here if specific update logic for items is needed.
// For now, RollTableUpdate uses RollTableItemCreate for its 'items' field, implying replacement.

export interface RollTable {
  id: number;
  name: string;
  description?: string | null;
  items: RollTableItem[];
  user_id?: number; // Added field
}

export interface RollTableCreate {
  name:string;
  description?: string | null;
  items: RollTableItemCreate[];
}

export interface RollTableUpdate {
  name?: string;
  description?: string | null;
  items?: RollTableItemCreate[]; // Allows replacing all items
}
