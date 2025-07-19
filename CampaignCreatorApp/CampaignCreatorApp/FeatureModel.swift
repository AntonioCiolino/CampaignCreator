import Foundation
import SwiftData

@Model
final class FeatureModel: Identifiable {
    @Attribute(.unique) var id: Int
    var name: String
    var template: String
    var user_id: Int?
    var required_context: [String]?
    var compatible_types: [String]?
    var feature_category: String?

    init(id: Int, name: String, template: String, user_id: Int?, required_context: [String]?, compatible_types: [String]?, feature_category: String?) {
        self.id = id
        self.name = name
        self.template = template
        self.user_id = user_id
        self.required_context = required_context
        self.compatible_types = compatible_types
        self.feature_category = feature_category
    }
}
