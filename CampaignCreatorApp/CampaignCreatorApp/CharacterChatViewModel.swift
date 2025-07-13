import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterChatViewModel: ObservableObject {
    @Published var chatMessages: [ChatMessage] = []
    @Published var isSendingMessage: Bool = false
    @Published var errorMessage: String?
    @Published var memorySummary: String? = "This is a placeholder for the actual memory summary."

    private let character: Character
    private var apiService = CampaignCreatorLib.APIService()

    init(character: Character) {
        self.character = character
        fetchChatHistory()
        fetchMemorySummary()
    }

    func clearChatMessages() {
        Task {
            do {
                try await apiService.performVoidRequest(endpoint: "/characters/\\(character.id)/chat", method: "DELETE")
                chatMessages.removeAll()
            } catch {
                errorMessage = "Failed to clear chat history: \\(error.localizedDescription)"
            }
        }
    }

    func fetchMemorySummary() {
        Task {
            do {
                let summary: MemorySummary = try await apiService.performRequest(endpoint: "/characters/\\(character.id)/memory-summary")
                self.memorySummary = summary.memory_summary
            } catch {
                self.errorMessage = "Failed to load memory summary: \\(error.localizedDescription)"
                self.memorySummary = "Could not load memory summary."
            }
        }
    }

    func fetchChatHistory() {
        Task {
            do {
                let apiMessages: [ConversationMessageEntry] = try await apiService.performRequest(endpoint: "/characters/\\(character.id)/chat")
                self.chatMessages = apiMessages.map { ChatMessage(from: $0, character: character) }
            } catch {
                self.errorMessage = "Failed to load chat history: \\(error.localizedDescription)"
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
            let tempChatMessages = self.chatMessages

            do {
                let historyForContextPayload = tempChatMessages.suffix(10).map { $0.toChatMessageData() }

                let aiResponse: CampaignCreatorLib.LLMTextResponseDTO = try await apiService.generateCharacterChatResponse(characterId: character.id, prompt: messageText, chatHistory: historyForContextPayload, modelIdWithPrefix: nil, temperature: nil, maxTokens: nil)

                let aiMessage = ChatMessage(
                    text: aiResponse.text,
                    sender: .llm,
                    character: character
                )
                self.chatMessages.append(aiMessage)
            } catch {
                self.errorMessage = "Error: \(error.localizedDescription)"
                self.chatMessages.removeAll { $0.id == optimisticUserMessage.id }
            }
            self.isSendingMessage = false
        }
    }
}
