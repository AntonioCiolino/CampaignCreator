import Foundation
import SwiftData

@Model
final class LLMModel: Identifiable {
    @Attribute(.unique) var id: String
    var name: String
    var model_type: String
    var supports_temperature: Bool
    var capabilities: [String]

    init(id: String, name: String, model_type: String, supports_temperature: Bool, capabilities: [String]) {
        self.id = id
        self.name = name
        self.model_type = model_type
        self.supports_temperature = supports_temperature
        self.capabilities = capabilities
    }
}
