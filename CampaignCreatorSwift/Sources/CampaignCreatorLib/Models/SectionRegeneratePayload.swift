import Foundation

// Matches 'SectionRegeneratePayload' in web UI's campaignTypes.ts
public struct SectionRegeneratePayload: Codable, Sendable {
    public var newPrompt: String?
    public var newTitle: String?
    public var sectionType: String?
    public var modelIdWithPrefix: String?
    public var featureId: Int?
    public var contextData: [String: String]? // Changed from [String: Any] to [String: String] for simplicity with current modal

    enum CodingKeys: String, CodingKey {
        case newPrompt = "new_prompt"
        case newTitle = "new_title"
        case sectionType = "section_type"
        case modelIdWithPrefix = "model_id_with_prefix"
        case featureId = "feature_id"
        case contextData = "context_data"
    }

    public init(newPrompt: String? = nil,
                newTitle: String? = nil,
                sectionType: String? = nil,
                modelIdWithPrefix: String? = nil,
                featureId: Int? = nil,
                contextData: [String: String]? = nil) {
        self.newPrompt = newPrompt
        self.newTitle = newTitle
        self.sectionType = sectionType
        self.modelIdWithPrefix = modelIdWithPrefix
        self.featureId = featureId
        self.contextData = contextData
    }
}
