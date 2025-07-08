import SwiftUI
import CampaignCreatorLib

struct ChatMessage: Identifiable, Equatable {
    let id = UUID()
    let text: String
    let sender: Sender

    enum Sender: String {
        case user = "User"
        case llm = "LLM"
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
                .disabled(userInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSendingMessage)
                .padding(.leading, 4)
            }
            .padding()
        }
        .navigationTitle("\(character.name) - Chat")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            // Optional: Add an initial greeting from the LLM based on the character?
            // For now, starts with an empty chat.
        }
    }

    private func sendMessage() {
        let messageText = userInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !messageText.isEmpty else { return }

        // Add user message to chat
        chatMessages.append(ChatMessage(text: messageText, sender: .user))
        userInput = ""
        isSendingMessage = true
        errorMessage = nil

        Task {
            do {
                // This function will be added to CampaignCreator
                let historyForAPI = chatMessages.map { msg in
                    CampaignCreatorLib.ChatMessageData(
                        text: msg.text,
                        sender: CampaignCreatorLib.ChatMessageData.Sender(rawValue: msg.sender.rawValue) ?? .user // Map sender
                    )
                }
                let llmResponse = try await campaignCreator.generateChatResponse(
                    character: character,
                    message: messageText,
                    chatHistory: historyForAPI // Pass mapped history
                )
                chatMessages.append(ChatMessage(text: llmResponse, sender: .llm))
            } catch {
                errorMessage = "Error: \(error.localizedDescription)"
                // Optionally, add an error message to the chatMessages array too
                // chatMessages.append(ChatMessage(text: "Error: Could not get response.", sender: .llm))
            }
            isSendingMessage = false
        }
    }
}

struct ChatMessageRow: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.sender == .user {
                Spacer()
                Text(message.text)
                    .padding(10)
                    .background(Color.blue.opacity(0.8))
                    .foregroundColor(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .frame(maxWidth: UIScreen.main.bounds.width * 0.7, alignment: .trailing)
            } else {
                Text(message.text)
                    .padding(10)
                    .background(Color.gray.opacity(0.3))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .frame(maxWidth: UIScreen.main.bounds.width * 0.7, alignment: .leading)
                Spacer()
            }
        }
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
        // Simulate some chat history for preview
        let sampleMessages = [
            ChatMessage(text: "Hello Aella!", sender: .user),
            ChatMessage(text: "Greetings, traveler. How may I assist you?", sender: .llm)
        ]

        NavigationView {
            CharacterChatView(
                campaignCreator: creator,
                character: sampleCharacter,
                chatMessages: sampleMessages // Pass initial messages for preview
            )
        }
    }
}
