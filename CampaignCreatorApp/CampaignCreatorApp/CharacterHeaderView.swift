import SwiftUI
import Kingfisher

struct CharacterHeaderView: View {
    let character: CharacterModel
    @Binding var editableName: String
    let isSaving: Bool
    let isGeneratingText: Bool
    let currentPrimaryColor: Color
    let onSetBadgeAction: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            TextField("Character Name", text: $editableName)
                .font(.largeTitle)
                .textFieldStyle(PlainTextFieldStyle())
                .padding(.bottom, 4)
                .disabled(isSaving || isGeneratingText)

            if let badgeUrlString = character.image_urls?.first, let badgeUrl = URL(string: badgeUrlString) {
                KFImage(badgeUrl)
                    .placeholder {
                        ProgressView().frame(width: 50, height: 50).padding(.top, 5)
                    }
                    .onFailure { error in
                        print("KFImage failed to load character badge \(badgeUrlString): \(error.localizedDescription)")
                    }
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(maxWidth: 50, maxHeight: 50)
                    .clipShape(Circle())
                    .overlay(Circle().stroke(currentPrimaryColor, lineWidth: 2))
                    .padding(.top, 5)
                    .id(character.image_urls?.first)
            } else {
                Image(systemName: "person.fill")
                    .font(.largeTitle)
                    .foregroundColor(.secondary)
                    .frame(width: 50, height: 50)
                    .padding(.top, 5)
            }
            Button(action: {
                onSetBadgeAction()
            }) {
                Text("Set Character Image")
            }
            .buttonStyle(.bordered)
            .font(.caption)
            .padding(.top, 2)

        }
        .padding().background(Color(.systemGroupedBackground)).cornerRadius(12)
    }
}

struct StatRow: View {
    let label: String
    let value: Int?

    var body: some View {
        HStack {
            Text(label)
            Spacer()
            Text("\(value ?? 0)")
        }
    }
}
