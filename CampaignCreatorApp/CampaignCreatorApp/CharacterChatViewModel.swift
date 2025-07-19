import Foundation
import SwiftUI
import SwiftData
import CampaignCreatorLib

@MainActor
class CharacterChatViewModel: ObservableObject {
    @Published var isSendingMessage: Bool = false
    @Published var errorMessage: String?

    private var character: CharacterModel
    private var apiService = CampaignCreatorLib.APIService()
    private var user: UserModel?
    private var memory: MemoryModel?
    private var modelContext: ModelContext

    init(character: CharacterModel, modelContext: ModelContext) {
        self.character = character
        self.modelContext = modelContext
        fetchCurrentUser()
    }

    private func fetchCurrentUser() {
        let descriptor = FetchDescriptor<UserModel>()
        if let user = try? modelContext.fetch(descriptor).first {
            self.user = user
            fetchOrCreateMemory()
        }
    }

    private func fetchOrCreateMemory() {
        guard let user = user else { return }
        let characterId = character.id
        let userId = user.id

        let predicate = #Predicate<MemoryModel> { memory in
            memory.character?.id == characterId && memory.user?.id == userId
        }
        let descriptor = FetchDescriptor(predicate: predicate)

        if let memory = try? modelContext.fetch(descriptor).first {
            self.memory = memory
        } else {
            let newMemory = MemoryModel(summary: "", timestamp: Date())
            newMemory.character = character
            newMemory.user = user
            modelContext.insert(newMemory)
            self.memory = newMemory
        }
        fetchChatHistory()
    }

    private func fetchChatHistory() {
        Task {
            do {
                let apiMessages: [ConversationMessageEntry] = try await apiService.performRequest(endpoint: "/characters/\(character.id)/chat")

                let existingMessageIds = Set((character.messages ?? []).map { $0.id })

                for apiMessage in apiMessages {
                    if !existingMessageIds.contains(apiMessage.id) {
                        let newMessage = ChatMessageModel(
                            text: apiMessage.text,
                            sender: apiMessage.speaker.lowercased() == "user" ? "user" : "llm",
                            timestamp: apiMessage.timestamp
                        )
                        newMessage.character = character
                        modelContext.insert(newMessage)
                    }
                }
                try? modelContext.save()

            } catch {
                self.errorMessage = "Failed to load chat history. Please check your connection and try again."
            }
        }
    }

    func clearChatMessages() {
        character.messages?.removeAll()
        try? modelContext.save()
    }

    func summarizeMemory() {
        // Now handled by observing the character model
    }

    func forceSummarizeMemory() {
        Task {
            do {
                let summary: MemorySummary = try await apiService.performRequest(endpoint: "/characters/\(character.id)/force-memory-summary", method: "POST")
                memory?.summary = summary.memory_summary ?? ""
                memory?.timestamp = Date()
                try? modelContext.save()
            } catch {
                errorMessage = "Failed to force memory summarization: \(error.localizedDescription)"
            }
        }
    }

    func sendMessage(userInput: String) {
        let messageText = userInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !messageText.isEmpty else { return }

        let userMessage = ChatMessageModel(text: messageText, sender: "user", timestamp: Date())
        userMessage.character = character
        modelContext.insert(userMessage)

        isSendingMessage = true
        errorMessage = nil

        Task {
            do {
                let history = (character.messages ?? []).suffix(10).map { msg -> ChatHistoryItem in
                    return ChatHistoryItem(speaker: msg.sender, text: msg.text)
                }

                let request = LLMTextGenerationParams(prompt: messageText, chat_history: history)
                let body = try JSONEncoder().encode(request)

                let aiResponse: LLMTextGenerationResponse = try await apiService.performRequest(endpoint: "/characters/\(character.id)/generate-response", method: "POST", body: body)

                let aiMessage = ChatMessageModel(text: aiResponse.text, sender: "llm", timestamp: Date())
                aiMessage.character = character
                modelContext.insert(aiMessage)

                try? modelContext.save()

            } catch {
                self.errorMessage = "Failed to send message. Please check your connection and try again."
                modelContext.delete(userMessage)
            }
            self.isSendingMessage = false
        }
    }
}
