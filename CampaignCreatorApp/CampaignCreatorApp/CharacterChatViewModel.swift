import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterChatViewModel: ObservableObject {
    @Published var chatMessages: [ChatMessage] = []
    @Published var isSendingMessage: Bool = false
    @Published var errorMessage: String?
    @Published var memorySummary: String?

    private let character: CharacterModel
    private var apiService = CampaignCreatorLib.APIService()
    private var user: User?

    init(character: CharacterModel) {
        self.character = character
        fetchData()
    }

    private func fetchData() {
        Task {
            await fetchUser()
            fetchChatHistory()
            fetchMemorySummary()
        }
    }

    private func fetchUser() async {
        do {
            self.user = try await apiService.performRequest(endpoint: "/users/me")
        } catch {
            errorMessage = "Failed to load user data."
        }
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

    func summarizeMemory() {
        fetchMemorySummary()
    }

    func forceSummarizeMemory() {
        Task {
            do {
                try await apiService.performVoidRequest(endpoint: "/characters/\(character.id)/force-memory-summary", method: "POST")
                fetchMemorySummary() // Re-fetch the summary to update the UI
            } catch {
                errorMessage = "Failed to force memory summarization: \(error.localizedDescription)"
            }
        }
    }

    func fetchMemorySummary() {
        Task {
            do {
                let summary: MemorySummary = try await apiService.performRequest(endpoint: "/characters/\(character.id)/memory-summary")
                self.memorySummary = summary.memory_summary ?? "No memory summary available."
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
                self.chatMessages = apiMessages.map { ChatMessage(from: $0, character: character, user: self.user) }
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
            character: character,
            user: self.user
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
                    character: character,
                    user: self.user
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
