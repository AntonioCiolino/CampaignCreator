// src/types/featureTypes.ts
export interface Feature {
  id: number;
  name: string;
  template: string;
  user_id?: number; // Changed to snake_case
}

export interface FeatureCreate {
  name: string;
  template: string;
}

export interface FeatureUpdate {
  name?: string;
  template?: string;
}
