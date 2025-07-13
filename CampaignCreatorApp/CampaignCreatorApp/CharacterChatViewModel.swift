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
            do {
                let request = CharacterAspectGenerationRequest(character_name: character.name, aspect_to_generate: "chat", existing_description: nil, existing_appearance_description: nil, notes_for_llm: nil, prompt_override: messageText, model_id_with_prefix: nil)
                let body = try JSONEncoder().encode(request)

                let aiResponse: CharacterAspectGenerationResponse = try await apiService.performRequest(endpoint: "/characters/\(character.id)/generate-aspect", method: "POST", body: body)

                let aiMessage = ChatMessage(
                    text: aiResponse.generated_text,
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
