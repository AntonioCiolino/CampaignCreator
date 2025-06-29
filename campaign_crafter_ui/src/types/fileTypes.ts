// Defines the structure for blob file metadata received from the backend

export interface BlobFileMetadata {
  name: string; // Base filename, e.g., "image.png"
  blob_name: string; // Full path in blob storage, e.g., "user_uploads/.../image.png"
  url: string; // Using string for URL on the frontend, Pydantic's HttpUrl validates on backend
  size: number; // Size in bytes
  last_modified: string; // ISO date string (e.g., "2023-10-27T10:30:00Z")
  content_type?: string;
}
