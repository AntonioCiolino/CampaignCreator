import Foundation
import CampaignCreatorLib // Import the library

// AvailableLLM and LLMModelsResponse are now defined in CampaignCreatorLib.
// This file can still provide placeholders or app-specific extensions if needed.

// Updated to use the type from CampaignCreatorLib.
// If CampaignCreatorLib is correctly imported, direct usage of AvailableLLM should work.
// If not, it might require CampaignCreatorLib.AvailableLLM explicitly.
public let placeholderLLMs: [CampaignCreatorLib.AvailableLLM] = [
    .init(id: "gpt-4", name: "GPT-4", model_type: "openai", supports_temperature: true, capabilities: ["text"]),
    .init(id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", model_type: "openai", supports_temperature: true, capabilities: ["text"]),
    .init(id: "claude-3-opus", name: "Claude 3 Opus", model_type: "anthropic", supports_temperature: true, capabilities: ["text"]),
    .init(id: "gemini-pro", name: "Gemini Pro", model_type: "google", supports_temperature: true, capabilities: ["text"])
]
// Note: Ensure the project settings correctly link CampaignCreatorLib so that this import works.
// The structs AvailableLLM and LLMModelsResponse are now expected to be resolved from CampaignCreatorLib.
