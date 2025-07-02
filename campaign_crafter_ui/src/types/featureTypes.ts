// src/types/featureTypes.ts
export interface Feature {
  id: number;
  name: string;
  template: string;
  user_id?: number;
  required_context?: string[]; // Added from backend model
  compatible_types?: string[]; // Added from backend model
}

export interface FeatureCreate {
  name: string;
  template: string;
  required_context?: string[];
  compatible_types?: string[];
}

export interface FeatureUpdate {
  name?: string;
  template?: string;
  required_context?: string[];
  compatible_types?: string[];
}
