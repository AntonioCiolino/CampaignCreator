import Foundation
import CampaignCreatorLib // Import the library

// AvailableLLM and LLMModelsResponse are now defined in CampaignCreatorLib.
// This file can still provide placeholders or app-specific extensions if needed.

// Updated to use the type from CampaignCreatorLib.
// If CampaignCreatorLib is correctly imported, direct usage of AvailableLLM should work.
// If not, it might require CampaignCreatorLib.AvailableLLM explicitly.
public let placeholderLLMs: [CampaignCreatorLib.AvailableLLM] = [
    .init(id: "gpt-4", name: "GPT-4", modelType: "openai", supportsTemperature: true, capabilities: ["text"], description: "The most powerful and capable model."),
    .init(id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", modelType: "openai", supportsTemperature: true, capabilities: ["text"], description: "A fast and affordable model."),
    .init(id: "claude-3-opus", name: "Claude 3 Opus", modelType: "anthropic", supportsTemperature: true, capabilities: ["text"], description: "A powerful model with a large context window."),
    .init(id: "gemini-pro", name: "Gemini Pro", modelType: "google", supportsTemperature: true, capabilities: ["text"], description: "A capable model from Google.")
]
// Note: Ensure the project settings correctly link CampaignCreatorLib so that this import works.
// The structs AvailableLLM and LLMModelsResponse are now expected to be resolved from CampaignCreatorLib.
