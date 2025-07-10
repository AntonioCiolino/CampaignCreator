import SwiftUI

struct CharacterImageManagerView: View {
    @Binding var imageURLs: [String]
    @Environment(\.dismiss) var dismiss

    @State private var newImageURL: String = ""
    @State private var showErrorAlert = false
    @State private var errorMessage = ""

    private func isValidURL(_ urlString: String) -> Bool {
        if urlString.isEmpty { return false }
        // Basic check for http/https prefix and some content after.
        // A more robust validation might involve regex or URLComponents.
        if let url = URL(string: urlString), (url.scheme == "http" || url.scheme == "https") {
            return UIApplication.shared.canOpenURL(url) // More thorough check if it looks like a typical web URL
        }
        // Allow simpler strings if they are just identifiers for local assets later,
        // but for now, assume web URLs. For a very basic check:
        // return urlString.lowercased().hasPrefix("http://") || urlString.lowercased().hasPrefix("https://")
        return URL(string: urlString) != nil // Basic check: can it be parsed as a URL?
    }

    private func addURL() {
        let trimmedURL = newImageURL.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedURL.isEmpty {
            errorMessage = "URL cannot be empty."
            showErrorAlert = true
            return
        }
        // More robust URL validation could be added here if needed
        if URL(string: trimmedURL) == nil {
             errorMessage = "Invalid URL format."
             showErrorAlert = true
             return
        }
        if imageURLs.contains(trimmedURL) {
            errorMessage = "This image URL has already been added."
            showErrorAlert = true
            return
        }
        imageURLs.append(trimmedURL)
        newImageURL = "" // Clear the field
    }

    private func deleteURLs(at offsets: IndexSet) {
        imageURLs.remove(atOffsets: offsets)
    }

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                HStack {
                    TextField("Enter new image URL", text: $newImageURL)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .autocapitalization(.none)
                        .keyboardType(.URL)
                    Button(action: addURL) {
                        Image(systemName: "plus.circle.fill")
                            .imageScale(.large)
                    }
                    .disabled(newImageURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
                .padding()

                List {
                    if imageURLs.isEmpty {
                        Text("No image URLs added yet. Add some above.")
                            .foregroundColor(.secondary)
                            .padding(.vertical)
                    } else {
                        ForEach(imageURLs, id: \.self) { urlString in
                            HStack {
                                AsyncImage(url: URL(string: urlString)) { phase in
                                    switch phase {
                                    case .empty:
                                        ProgressView()
                                    case .success(let image):
                                        image.resizable()
                                            .aspectRatio(contentMode: .fill)
                                    case .failure:
                                        Image(systemName: "photo.fill")
                                            .foregroundColor(.gray)
                                    @unknown default:
                                        EmptyView()
                                    }
                                }
                                .frame(width: 44, height: 44)
                                .clipShape(RoundedRectangle(cornerRadius: 4))
                                .background(Color.gray.opacity(0.1))

                                Text(urlString)
                                    .font(.caption)
                                    .lineLimit(1)
                                    .truncationMode(.middle)
                                Spacer() // Pushes delete button to the right if we add one explicitly
                            }
                        }
                        .onDelete(perform: deleteURLs)
                    }
                }
                .listStyle(InsetGroupedListStyle()) // Or .plain for a simpler look
            }
            .navigationTitle("Manage Images")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .navigationBarLeading) {
                    if !imageURLs.isEmpty { EditButton() } // Show EditButton only if there are items
                }
            }
            .alert("Error", isPresented: $showErrorAlert) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }
}

struct CharacterImageManagerView_Previews: PreviewProvider {
    struct PreviewWrapper: View {
        @State var urls: [String] = [
            "https://picsum.photos/seed/img1/50/50",
            "https://picsum.photos/seed/img2/50/50",
            "http://example.com/another-image.png"
        ]
        @State var emptyUrls: [String] = []

        var body: some View {
            VStack {
                Text("Tap button to show manager")
                Button("Show Image Manager (With URLs)") {
                    // This doesn't work directly in previews like a sheet presentation would
                }
                CharacterImageManagerView(imageURLs: $urls) // Direct preview

                Button("Show Image Manager (Empty)") {
                }
                CharacterImageManagerView(imageURLs: $emptyUrls) // Direct preview
            }
        }
    }

    static var previews: some View {
        PreviewWrapper()
        // For a sheet-like preview, you'd need a state to control presentation:
        // CharacterImageManagerView(imageURLs: .constant(["https://picsum.photos/seed/preview/50/50"]))
    }
}
