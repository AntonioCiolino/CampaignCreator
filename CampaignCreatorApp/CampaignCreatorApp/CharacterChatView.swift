import SwiftUI
import Kingfisher
import SwiftData
import CampaignCreatorLib

struct CharacterChatView: View {
    @StateObject private var viewModel: CharacterChatViewModel
    @State private var userInput: String = ""
    @Bindable var character: CharacterModel
    @Environment(\.modelContext) private var modelContext

    private var sortedMessages: [ChatMessageModel] {
        (character.messages ?? []).sorted { $0.timestamp < $1.timestamp }
    }

    init(character: CharacterModel) {
        self.character = character
        _viewModel = StateObject(wrappedValue: CharacterChatViewModel(character: character, modelContext: PersistenceController.shared.container.mainContext))
    }

    @State private var showingMemoryView = false

    var body: some View {
        VStack {
            ScrollViewReader { scrollViewProxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(sortedMessages) { message in
                            ChatMessageRow(message: message, character: character)
                                .id(message.id)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 8)
                }
                .onChange(of: sortedMessages) {
                    if let lastMessage = sortedMessages.last {
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
                    .onSubmit {
                        viewModel.sendMessage(userInput: userInput)
                        userInput = ""
                    }

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
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button(action: {
                    showingMemoryView = true
                }) {
                    Image(systemName: "brain")
                }

                Button(action: {
                    viewModel.clearChatMessages()
                }) {
                    Image(systemName: "trash")
                }
            }
        }
        .sheet(isPresented: $showingMemoryView) {
            MemoryView(viewModel: MemoryViewModel(character: character, modelContext: modelContext))
        }

    }
}

struct ChatMessageRow: View {
    let message: ChatMessageModel
    let character: CharacterModel

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if message.sender == "llm" {
                AvatarView(url: URL(string: character.image_urls?.first ?? ""))
                MessageBubble(text: message.text, isUser: false)
                Spacer()
            } else {
                Spacer()
                MessageBubble(text: message.text, isUser: true)
                // We'll need to fetch the user's avatar URL from somewhere
                AvatarView(url: nil)
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


//struct CharacterChatView_Previews: PreviewProvider {
//    static var previews: some View {
//        let libCharacter = CampaignCreatorLib.Character(id: 1, name: "Aella Chat Preview")
//        let sampleCharacter = Character(from: libCharacter)
//
//        return NavigationView {
//            CharacterChatView(character: sampleCharacter)
//        }
//    }
//}
