import Foundation

// This struct is for passing chat message data (context) to the backend /generate-response endpoint.
// It should match the backend's Pydantic model: `ConversationMessageContext {speaker: str, text: str}`.
public struct ChatMessageData: Codable, Sendable {
    public let speaker: String // Should be "user" or "assistant"
    public let text: String

    public init(speaker: String, text: String) {
        self.speaker = speaker
        self.text = text
    }
}
// The old Sender enum is removed as 'speaker' is now a direct String.
// The mapping from the UI's ChatMessage.Sender enum to these speaker strings ("user", "assistant")
// will occur in CharacterChatView.swift when preparing this payload.
