import SwiftUI
import Kingfisher

struct CharacterHeaderView: View {
    let character: CharacterModel
    @Binding var editableName: String
    let isSaving: Bool
    let isGeneratingText: Bool
    let currentPrimaryColor: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(character.name)
                .font(.largeTitle)
                .padding(.bottom, 4)

            if let badgeUrlString = character.image_urls?.first, let badgeUrl = URL(string: badgeUrlString) {
                if badgeUrl.isFileURL {
                    if let imageData = try? Data(contentsOf: badgeUrl), let uiImage = UIImage(data: imageData) {
                        Image(uiImage: uiImage)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(maxWidth: 50, maxHeight: 50)
                            .clipShape(Circle())
                            .overlay(Circle().stroke(currentPrimaryColor, lineWidth: 2))
                            .padding(.top, 5)
                    } else {
                        Image(systemName: "person.fill")
                            .font(.largeTitle)
                            .foregroundColor(.secondary)
                            .frame(width: 50, height: 50)
                            .padding(.top, 5)
                    }
                } else {
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
                }
            } else {
                Image(systemName: "person.fill")
                    .font(.largeTitle)
                    .foregroundColor(.secondary)
                    .frame(width: 50, height: 50)
                    .padding(.top, 5)
            }
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
