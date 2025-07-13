import SwiftUI
import Kingfisher

struct ChatMessage: Identifiable, Equatable {
    let id: String
    let text: String
    let sender: Sender
    let timestamp: Date
    let userAvatarUrl: URL?
    let characterAvatarUrl: URL?

    enum Sender: String {
        case user = "User"
        case llm = "LLM"
    }

    init(from apiMessage: ConversationMessageEntry, character: Character) {
        self.id = UUID().uuidString
        self.text = apiMessage.text
        self.timestamp = apiMessage.timestamp

        if apiMessage.speaker.lowercased() == "user" {
            self.sender = .user
        } else {
            self.sender = .llm
        }

        self.userAvatarUrl = nil
        self.characterAvatarUrl = (self.sender == .llm) ? URL(string: character.image_urls?.first ?? "") : nil
    }

    init(text: String, sender: Sender, character: Character) {
        self.id = UUID().uuidString
        self.text = text
        self.sender = sender
        self.timestamp = Date()
        self.userAvatarUrl = nil
        self.characterAvatarUrl = (self.sender == .llm) ? URL(string: character.image_urls?.first ?? "") : nil
    }
}

struct CharacterChatView: View {
    @StateObject private var viewModel: CharacterChatViewModel
    @State private var userInput: String = ""

    init(character: Character) {
        _viewModel = StateObject(wrappedValue: CharacterChatViewModel(character: character))
    }

    var body: some View {
        VStack {
            if let summary = viewModel.memorySummary, !summary.isEmpty {
                MemorySummaryView(memorySummary: summary)
                    .padding(.horizontal)
            }

            ScrollViewReader { scrollViewProxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.chatMessages) { message in
                            ChatMessageRow(message: message)
                                .id(message.id)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 8)
                }
                .onChange(of: viewModel.chatMessages) { _ in
                    if let lastMessage = viewModel.chatMessages.last {
                        withAnimation {
                            scrollViewProxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            if let error = viewModel.errorMessage {
                Text(error)
                    .foregroundColor(.red)
                    .padding(.horizontal)
                    .font(.caption)
            }

            HStack {
                TextField("Type your message...", text: $userInput, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...5)
                    .disabled(viewModel.isSendingMessage)

                Button(action: {
                    viewModel.sendMessage(userInput: userInput)
                    userInput = ""
                }) {
                    if viewModel.isSendingMessage {
                        ProgressView()
                            .frame(width: 24, height: 24)
                    } else {
                        Image(systemName: "paperplane.fill")
                    }
                }
                .disabled(userInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSendingMessage)
                .padding(.leading, 4)
            }
            .padding()
        }
        .navigationTitle("Chat")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(action: {
                    viewModel.clearChatMessages()
                }) {
                    Image(systemName: "trash")
                }
            }
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
            } else {
                Spacer()
                MessageBubble(text: message.text, isUser: true)
                AvatarView(url: message.userAvatarUrl)
            }
        }
        .padding(.horizontal, 8)
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
        let sampleCharacter = Character(
            id: 1,
            owner_id: 1,
            name: "Aella Chat Preview",
            description: "A nimble scout.",
            appearance_description: "Slender build.",
            image_urls: [],
            video_clip_urls: [],
            notes_for_llm: "Loves nature.",
            stats: nil,
            export_format_preference: nil
        )

        return NavigationView {
            CharacterChatView(character: sampleCharacter)
        }
    }
}
