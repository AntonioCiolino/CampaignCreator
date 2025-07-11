import Foundation

// Note: This is now part of CampaignCreatorLib
// Ensure CampaignCreatorApp/CampaignCreatorApp/LLMModels.swift is updated or removed
// to avoid type conflicts and to use this central definition.

public struct AvailableLLM: Identifiable, Codable, Hashable {
    public var id: String // Prefixed ID, e.g., "openai/gpt-3.5-turbo"
    public var name: String // User-friendly name, e.g., "OpenAI GPT-3.5 Turbo"
    public var model_type: String
    public var supports_temperature: Bool
    public var capabilities: [String]?

    // Public initializer is needed if this struct is to be created from other modules.
    public init(id: String, name: String, model_type: String, supports_temperature: Bool, capabilities: [String]? = nil) {
        self.id = id
        self.name = name
        self.model_type = model_type
        self.supports_temperature = supports_temperature
        self.capabilities = capabilities
    }
}

// Structure for the API response, also part of CampaignCreatorLib
public struct LLMModelsResponse: Codable {
    public var models: [AvailableLLM]

    // Public initializer might be useful for testing or other scenarios.
    public init(models: [AvailableLLM]) {
        self.models = models
    }
}
