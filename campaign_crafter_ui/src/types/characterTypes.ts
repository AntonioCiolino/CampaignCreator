/**
 * Represents a single image associated with a character.
 * Corresponds to the CharacterImage Pydantic model.
 */
export interface CharacterImage {
  url: string; // HttpUrl is a string in TypeScript
  caption?: string | null;
  // Future fields: uploaded_at, tags, etc.
}

/**
 * Base interface for character data.
 * Corresponds to the CharacterBase Pydantic model.
 */
export interface CharacterBase {
  name: string;
  icon_url?: string | null; // HttpUrl is a string
  stats?: Record<string, string> | null; // Dict[str, str] becomes Record<string, string>
  notes?: string | null;
  chatbot_enabled?: boolean | null;
  campaign_id: number; // Assuming campaign_id is always a number
}

/**
 * Interface for creating a new character.
 * Corresponds to the CharacterCreate Pydantic model.
 */
export interface CharacterCreatePayload extends Omit<CharacterBase, 'campaign_id'> { // campaign_id will be part of the URL path
  images?: CharacterImage[] | null;
}

/**
 * Interface for updating an existing character (all fields optional).
 * Corresponds to the CharacterUpdate Pydantic model.
 */
export interface CharacterUpdatePayload {
  name?: string | null;
  icon_url?: string | null;
  stats?: Record<string, string> | null;
  notes?: string | null;
  chatbot_enabled?: boolean | null;
  images?: CharacterImage[] | null; // Allow updating the list of images
}

/**
 * Full character data including its ID, as returned by the API.
 * Corresponds to the Character Pydantic model.
 */
export interface PydanticCharacter extends CharacterBase {
  id: number;
  images: CharacterImage[]; // List of image objects
}

// Example of how you might use these types in a component state or prop:
//
// interface CharacterEditorProps {
//   character?: PydanticCharacter; // For editing an existing character
//   campaignId: number;
//   onSave: (characterData: PydanticCharacter) => void;
// }
//
// const [formData, setFormData] = useState<CharacterCreatePayload | CharacterUpdatePayload>({});
