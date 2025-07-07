import Foundation

// Matches 'Feature' interface in featureTypes.ts (web UI)
public struct Feature: Codable, Identifiable, Sendable, Hashable {
    public let id: Int
    public let name: String
    public let template: String
    public let userId: Int?
    public let requiredContext: [String]?
    public let compatibleTypes: [String]?
    public let featureCategory: String?

    enum CodingKeys: String, CodingKey {
        case id, name, template
        case userId = "user_id"
        case requiredContext = "required_context"
        case compatibleTypes = "compatible_types"
        case featureCategory = "feature_category"
    }

    public init(id: Int, name: String, template: String, userId: Int? = nil, requiredContext: [String]? = nil, compatibleTypes: [String]? = nil, featureCategory: String? = nil) {
        self.id = id
        self.name = name
        self.template = template
        self.userId = userId
        self.requiredContext = requiredContext
        self.compatibleTypes = compatibleTypes
        self.featureCategory = featureCategory
    }
}
