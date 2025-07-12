import SwiftUI
import Kingfisher

struct FullCharacterImageView: View {
    @Binding var imageURL: URL?
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            VStack {
                if let url = imageURL {
                    KFImage(url)
                        .placeholder {
                            ProgressView("Loading Image...")
                        }
                        .onFailure { error in
                            print("KFImage failed to load full character image \(url.absoluteString): \(error.localizedDescription)")
                        }
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .padding()
                } else {
                    Text("No image URL provided.")
                    Image(systemName: "photo.fill")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 100, height: 100)
                        .foregroundColor(.gray)
                }
                Spacer()
            }
            .navigationTitle("Character Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        imageURL = nil
                        dismiss()
                    }
                }
                ToolbarItem(placement: .bottomBar) {
                    if let url = imageURL {
                        Button(action: {
                            UIApplication.shared.open(url)
                        }) {
                            Label("Open in Browser", systemImage: "safari.fill")
                        }
                        .disabled(imageURL == nil)
                    } else {
                        EmptyView()
                    }
                }
            }
        }
    }
}
