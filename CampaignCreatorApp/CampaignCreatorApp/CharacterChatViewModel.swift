import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterChatViewModel: ObservableObject {
    @Published var chatMessages: [ChatMessage] = []
    @Published var isSendingMessage: Bool = false
    @Published var errorMessage: String?
    @Published var memorySummary: String? = "This is a placeholder for the actual memory summary."

    private let character: CharacterModel
    private var apiService = CampaignCreatorLib.APIService()

    init(character: CharacterModel) {
        self.character = character
        fetchChatHistory()
        fetchMemorySummary()
    }

    func clearChatMessages() {
        Task {
            do {
                try await apiService.performVoidRequest(endpoint: "/characters/\(character.id)/chat", method: "DELETE")
                chatMessages.removeAll()
            } catch {
                errorMessage = "Failed to clear chat history: \(error.localizedDescription)"
            }
        }
    }

    func fetchMemorySummary() {
        Task {
            do {
                let summary: MemorySummary = try await apiService.performRequest(endpoint: "/characters/\(character.id)/memory-summary")
                self.memorySummary = summary.memory_summary
            } catch {
                self.errorMessage = "Failed to load memory summary. Please check your connection and try again."
                self.memorySummary = "Could not load memory summary."
            }
        }
    }

    func fetchChatHistory() {
        Task {
            do {
                let apiMessages: [ConversationMessageEntry] = try await apiService.performRequest(endpoint: "/characters/\(character.id)/chat")
                self.chatMessages = apiMessages.map { ChatMessage(from: $0, character: character) }
            } catch {
                self.errorMessage = "Failed to load chat history. Please check your connection and try again."
            }
        }
    }

    func sendMessage(userInput: String) {
        let messageText = userInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !messageText.isEmpty else { return }

        let optimisticUserMessage = ChatMessage(
            text: messageText,
            sender: .user,
            character: character
        )
        chatMessages.append(optimisticUserMessage)

        isSendingMessage = true
        errorMessage = nil

        Task {
            do {
                let history = chatMessages.suffix(10).map { msg -> ChatHistoryItem in
                    let speaker = msg.sender == .user ? "user" : "assistant"
                    return ChatHistoryItem(speaker: speaker, text: msg.text)
                }

                let request = LLMTextGenerationParams(prompt: messageText, chat_history: history)
                let body = try JSONEncoder().encode(request)

                let aiResponse: LLMTextGenerationResponse = try await apiService.performRequest(endpoint: "/characters/\(character.id)/generate-response", method: "POST", body: body)

                let aiMessage = ChatMessage(
                    text: aiResponse.text,
                    sender: .llm,
                    character: character
                )
                self.chatMessages.append(aiMessage)
            } catch {
                self.errorMessage = "Failed to send message. Please check your connection and try again."
                self.chatMessages.removeAll { $0.id == optimisticUserMessage.id }
            }
            self.isSendingMessage = false
        }
    }
}
