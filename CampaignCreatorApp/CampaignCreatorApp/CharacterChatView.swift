import SwiftUI
import CampaignCreatorLib
import Kingfisher
// Assuming this library contains the updated APIService and models

struct ChatMessage: Identifiable, Equatable {
    let id: String // Changed to String, typically a UUID for local, or derived from APIChatMessage.id
    let text: String
    let sender: Sender // UI-specific enum for sender type
    let timestamp: Date
    let userAvatarUrl: URL?
    let characterAvatarUrl: URL?

    enum Sender: String {
        case user = "User"
        case llm = "LLM"
    }

    // Initializer from the new APIChatMessage (which is {speaker, text, timestamp})
    init(from apiMessage: CampaignCreatorLib.APIChatMessage, character: Character, currentUser: User?) {
        self.id = apiMessage.id // The computed 'id' from APIChatMessage is used here
        self.text = apiMessage.text
        self.timestamp = apiMessage.timestamp

        // Derive local Sender enum from apiMessage.speaker
        if apiMessage.speaker.lowercased() == "user" {
            self.sender = .user
        } else { // "assistant" or character name maps to .llm
            self.sender = .llm
        }

        // Avatar logic remains similar, based on derived sender
        self.userAvatarUrl = (self.sender == .user) ? URL(string: currentUser?.avatarUrl ?? "") : nil
        self.characterAvatarUrl = (self.sender == .llm) ? URL(string: character.imageURLs?.first ?? "") : nil
    }

    // Initializer for optimistic updates (e.g., user-sent messages before backend confirmation)
    // or for AI messages created directly from LLM text response.
    init(id: String = UUID().uuidString, text: String, sender: Sender, timestamp: Date = Date(), userAvatarUrl: URL? = nil, characterAvatarUrl: URL? = nil) {
        self.id = id
        self.text = text
        self.sender = sender
        self.timestamp = timestamp
        self.userAvatarUrl = userAvatarUrl
        self.characterAvatarUrl = characterAvatarUrl
    }
}

struct CharacterChatView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    var character: Character

    @State private var userInput: String = ""
    @State private var chatMessages: [ChatMessage] = []
    @State private var isSendingMessage: Bool = false
    @State private var errorMessage: String? = nil
    @State private var memorySummary: String? = "This is a placeholder for the actual memory summary."
    @State private var showingMemorySummary = false

    var body: some View {
        VStack {
            // Chat messages display area
            ScrollViewReader { scrollViewProxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(chatMessages) { message in
                            ChatMessageRow(message: message)
                                .id(message.id)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 8)
                }
                .onChange(of: chatMessages) { _ in
                    if let lastMessage = chatMessages.last {
                        withAnimation {
                            scrollViewProxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            // Error message display
            if let error = errorMessage {
                Text(error)
                    .foregroundColor(.red)
                    .padding(.horizontal)
                    .font(.caption)
            }

            // Input area
            HStack {
                TextField("Type your message...", text: $userInput, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...5)
                    .disabled(isSendingMessage)

                Button(action: sendMessage) {
                    if isSendingMessage {
                        ProgressView()
                            .frame(width: 24, height: 24)
                    } else {
                        Image(systemName: "paperplane.fill")
                    }
                }
                .disabled(userInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSendingMessage || !campaignCreator.isLLMServiceAvailable)
                .padding(.leading, 4)
            }
            .padding()
            if !campaignCreator.isLLMServiceAvailable {
                Text("Chat requires OpenAI API key configuration in settings.")
                    .font(.caption)
                    .foregroundColor(.orange)
                    .padding(.horizontal)
                    .multilineTextAlignment(.center)
            }
        }
        .navigationTitle("\(character.name) - Chat")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack {
                    Button(action: {
                        showingMemorySummary.toggle()
                    }) {
                        Image(systemName: "brain.head.profile")
                    }
                    .disabled(memorySummary == nil || memorySummary!.isEmpty)

                    Button(action: {
                        // Action to clear chat
                        clearChatMessages()
                    }) {
                        Image(systemName: "trash")
                    }
                }
            }
        }
        .sheet(isPresented: $showingMemorySummary) {
            MemorySummaryView(memorySummary: memorySummary ?? "No summary available.")
        }
        .onAppear {
            fetchChatHistory()
            fetchMemorySummary()
        }
    }

    private func clearChatMessages() {
        Task {
            do {
                try await campaignCreator.clearChatHistory(characterId: character.id)
                await MainActor.run {
                    chatMessages.removeAll()
                    // Optionally, show a success message to the user
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Failed to clear chat history: \(error.localizedDescription)"
                }
            }
        }
    }

    private func fetchMemorySummary() {
        Task {
            do {
                // Assuming an API service call that fetches the memory summary for a character.
                // This is a placeholder for the actual implementation.
                let summary = try await campaignCreator.apiService.getMemorySummary(characterId: character.id)
                self.memorySummary = summary
            } catch {
                // Handle error, maybe show a default message or hide the view
                self.errorMessage = "Failed to load memory summary: \(error.localizedDescription)"
                self.memorySummary = "Could not load memory summary."
            }
        }
    }

    private func fetchChatHistory() {
        Task {
            do {
                let apiMessages = try await campaignCreator.apiService.getChatHistory(characterId: character.id)
                // Assuming campaignCreator.currentUser is available. If not, this needs adjustment.
                let currentUser = campaignCreator.currentUser
                self.chatMessages = apiMessages.map { ChatMessage(from: $0, character: character, currentUser: currentUser) }
            } catch {
                self.errorMessage = "Failed to load chat history: \(error.localizedDescription)"
            }
        }
    }

    private func sendMessage() {
        let messageText = userInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !messageText.isEmpty else { return }

        // 1. Optimistic User Message (ID is now String via UUID)
        let optimisticUserMessage = ChatMessage(
            // id will be UUID().uuidString by default initializer
            text: messageText,
            sender: .user,
            timestamp: Date(),
            userAvatarUrl: URL(string: campaignCreator.currentUser?.avatarUrl ?? ""),
            characterAvatarUrl: URL(string: character.imageURLs?.first ?? "")
        )
        chatMessages.append(optimisticUserMessage)

        let currentInput = userInput // Store before clearing
        userInput = "" // Clear input field
        isSendingMessage = true
        errorMessage = nil

        Task {
            let tempChatMessages = self.chatMessages // Capture current state for context

            do {
                // 2. Prepare historyForLLMService (map to CampaignCreatorLib.ChatMessageData {speaker: String, text: String})
                // Send up to last 10 messages from the current UI state for context.
                // The current user's message is already in tempChatMessages.
                let historyForContextPayload = tempChatMessages.suffix(10).map { uiMsg -> CampaignCreatorLib.ChatMessageData in
                    let speakerText = uiMsg.sender == .user ? "user" : "assistant" // Map enum to string
                    return CampaignCreatorLib.ChatMessageData(speaker: speakerText, text: uiMsg.text)
                }

                // 3. Call generateChatResponse - this should now return the AI's response text
                // Assuming campaignCreator.generateChatResponse and APIService.generateCharacterChatResponse
                // are updated to accept modelId, temperature, maxTokens.
                // For now, passing nil for those, assuming APIService method has defaults or they are not yet implemented in CampaignCreator.
                let aiResponseDTO = try await campaignCreator.generateChatResponse( // Expects LLMTextResponseDTO
                    character: character,
                    message: currentInput,
                    chatHistory: historyForContextPayload, // Pass history *including* current user prompt for LLM service
                    modelIdWithPrefix: nil, // Placeholder for actual model selection UI
                    temperature: nil,       // Placeholder
                    maxTokens: nil          // Placeholder
                )
                let aiResponseText = aiResponseDTO.text

                // 4. Optimistic AI Message
                let aiMessage = ChatMessage(
                    // id will be UUID().uuidString by default
                    text: aiResponseText,
                    sender: .llm,
                    timestamp: Date(), // Use current time, or server time if DTO provided it
                    userAvatarUrl: nil,
                    characterAvatarUrl: URL(string: character.imageURLs?.first ?? "")
                )
                self.chatMessages.append(aiMessage)

                // 5. Optional: Fetch full history in background to reconcile if needed,
                // but not strictly necessary for displaying this turn's AI response.
                // If backend persistence is slow, this might still overwrite the optimistic AI message
                // with an older state if not handled carefully.
                // For now, let's rely on the direct response and the onAppear fetch.
                // fetchChatHistory() // Consider if this is needed or if it causes issues.

            } catch {
                self.errorMessage = "Error: \(error.localizedDescription)"
                // If AI response failed, remove the optimistic USER message as the exchange failed.
                self.chatMessages.removeAll { $0.id == optimisticUserMessage.id }
                self.userInput = currentInput // Restore user input
            }
            self.isSendingMessage = false
        }
    }
}

struct ChatMessageRow: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if message.sender == .llm {
                AvatarView(url: message.characterAvatarUrl)
                MessageBubble(text: message.text, isUser: false)
                Spacer()
            } else { // User message
                Spacer()
                MessageBubble(text: message.text, isUser: true)
                AvatarView(url: message.userAvatarUrl)
            }
        }
        .padding(.horizontal, 8) // Add some horizontal padding to the row itself
    }
}

struct AvatarView: View {
    let url: URL?

    var body: some View {
        KFImage(url)
            .placeholder {
                Image(systemName: "person.circle.fill")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .foregroundColor(.gray)
            }
            .resizable()
            .aspectRatio(contentMode: .fill)
            .frame(width: 30, height: 30)
            .clipShape(Circle())
            .overlay(Circle().stroke(Color.gray.opacity(0.5), lineWidth: 0.5))
    }
}

struct MessageBubble: View {
    let text: String
    let isUser: Bool

    var body: some View {
        Text(text)
            .padding(10)
            .background(isUser ? Color.blue.opacity(0.8) : Color.gray.opacity(0.25))
            .foregroundColor(isUser ? .white : .primary)
            .clipShape(RoundedRectangle(cornerRadius: 15))
            .frame(maxWidth: UIScreen.main.bounds.width * 0.7, alignment: isUser ? .trailing : .leading)
    }
}


struct CharacterChatView_Previews: PreviewProvider {
    static var previews: some View {
        let creator = CampaignCreator()
        let sampleCharacter = Character(
            id: 1,
            name: "Aella Chat Preview",
            description: "A nimble scout.",
            appearanceDescription: "Slender build.",
            notesForLLM: "Loves nature."
        )

        // let sampleMessages = [ // REMOVED as it was unused
        //     ChatMessage(text: "Hello Aella!", sender: .user),
        //     ChatMessage(text: "Greetings, traveler. How may I assist you?", sender: .llm)
        // ]

        return NavigationView {
            CharacterChatView(
                campaignCreator: creator,
                character: sampleCharacter
            )
        }
    }
}
