import SwiftUI
import CampaignCreatorLib

struct ChatMessage: Identifiable, Equatable {
    let id: Int // Changed from UUID to Int to match APIChatMessage
    let text: String
    let sender: Sender
    let timestamp: Date // Added timestamp
    let userAvatarUrl: URL? // Added for thumbnail
    let characterAvatarUrl: URL? // Added for thumbnail

    enum Sender: String {
        case user = "User"
        case llm = "LLM" // Represents the character/LLM
    }

    // Initializer from APIChatMessage
    init(from apiMessage: CampaignCreatorLib.APIChatMessage, character: Character, currentUser: User?) {
        self.id = apiMessage.id
        self.text = apiMessage.text
        self.timestamp = apiMessage.timestamp

        if apiMessage.sender.lowercased() == "user" {
            self.sender = .user
        } else { // Assume other sender is LLM/character
            self.sender = .llm
        }

        self.userAvatarUrl = URL(string: currentUser?.avatarUrl ?? "")
        self.characterAvatarUrl = URL(string: character.imageURLs?.first ?? "")
    }

    // Original initializer for optimistic updates (if needed) or previews
    init(id: Int? = nil, text: String, sender: Sender, timestamp: Date? = nil, userAvatarUrl: URL? = nil, characterAvatarUrl: URL? = nil) {
        self.id = id ?? Int.random(in: 1_000_000...2_000_000) // Temporary ID for optimistic updates
        self.text = text
        self.sender = sender
        self.timestamp = timestamp ?? Date()
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
        .onAppear {
            fetchChatHistory()
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

        let optimisticUserMessage = ChatMessage(
            text: messageText,
            sender: .user,
            userAvatarUrl: URL(string: campaignCreator.currentUser?.avatarUrl ?? ""), // Placeholder if no user
            characterAvatarUrl: URL(string: character.imageURLs?.first ?? "")
        )
        chatMessages.append(optimisticUserMessage)

        let currentInput = userInput
        userInput = ""
        isSendingMessage = true
        errorMessage = nil

        Task {
            do {
                // The backend /generate-response endpoint now handles saving messages and using DB history.
                // We send the current user prompt.
                // The chatHistory parameter in generateChatResponse is for client-side context if needed by LLM immediately,
                // but primary history context is now from backend DB.
                // For this call, we can pass a limited recent history if the function expects it,
                // or an empty array if it's truly just for the current prompt.

                let historyForLLMService = chatMessages.suffix(10).map { msg in // Send recent messages
                    CampaignCreatorLib.ChatMessageData(
                        text: msg.text,
                        sender: CampaignCreatorLib.ChatMessageData.Sender(rawValue: msg.sender.rawValue) ?? .user
                    )
                }

                _ = try await campaignCreator.generateChatResponse( // We don't need the direct response text here
                    character: character,
                    message: currentInput, // Send the current message text
                    chatHistory: historyForLLMService
                )

                // After the backend processes and saves, fetch the updated history.
                fetchChatHistory()

            } catch {
                errorMessage = "Error: \(error.localizedDescription)"
                // Optionally, remove optimistic message if send failed catastrophically
                // chatMessages.removeAll { $0.id == optimisticUserMessage.id }
            }
            isSendingMessage = false
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
        Group {
            if let url = url {
                AsyncImage(url: url) { phase in
                    if let image = phase.image {
                        image.resizable()
                            .aspectRatio(contentMode: .fill)
                    } else if phase.error != nil {
                        Image(systemName: "person.circle.fill") // Error placeholder
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .foregroundColor(.gray)
                    } else {
                        ProgressView() // Loading placeholder
                    }
                }
            } else {
                Image(systemName: "person.circle.fill") // Default placeholder
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .foregroundColor(.gray)
            }
        }
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
