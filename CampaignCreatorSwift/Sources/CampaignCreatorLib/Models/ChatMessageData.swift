import Foundation

// This struct is for passing chat message data to CampaignCreator functions
// It mirrors the structure of ChatMessage in the App module but lives in the Lib.
public struct ChatMessageData: Sendable {
    public let text: String
    public let sender: Sender

    public enum Sender: String, Sendable {
        case user = "User"
        case llm = "LLM"
    }

    public init(text: String, sender: Sender) {
        self.text = text
        self.sender = sender
    }
}
