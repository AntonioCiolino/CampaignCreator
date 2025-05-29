export interface CampaignSectionCreatePayload {
  title?: string;
  prompt?: string;
  modelId?: string; // Add this line if you want to support modelId
}