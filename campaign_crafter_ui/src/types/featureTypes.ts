// src/types/featureTypes.ts
export interface Feature {
  id: number;
  name: string;
  template: string;
  user_id?: number;
  required_context?: string[];
  compatible_types?: string[];
  feature_category?: string; // Added field
}

export interface FeatureCreate {
  name: string;
  template: string;
  required_context?: string[];
  compatible_types?: string[];
  feature_category?: string; // Added field
}

export interface FeatureUpdate {
  name?: string;
  template?: string;
  required_context?: string[];
  compatible_types?: string[];
  feature_category?: string; // Added field
}
