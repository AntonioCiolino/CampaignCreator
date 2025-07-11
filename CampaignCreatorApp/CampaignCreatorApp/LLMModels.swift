import Foundation

public struct AvailableLLM: Identifiable, Codable, Hashable {
    public var id: String
    public var name: String

    public init(id: String, name: String) {
        self.id = id
        self.name = name
    }
}

public let placeholderLLMs: [AvailableLLM] = [
    AvailableLLM(id: "gpt-4", name: "GPT-4"),
    AvailableLLM(id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo"),
    AvailableLLM(id: "claude-3-opus", name: "Claude 3 Opus"),
    AvailableLLM(id: "gemini-pro", name: "Gemini Pro")
]
