import SwiftUI
import CampaignCreatorLib // Required for ImageModelName, ImageGenerationParams, APIService

struct CharacterImageManagerView: View {
    @Binding var imageURLs: [String]
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var apiService: APIService // Assuming APIService is an EnvironmentObject

    // For manual URL entry
    @State private var newImageURL: String = ""

    // For AI Image Generation
    @State private var imagePrompt: String = ""
    @State private var selectedModel: ImageModelName = .openAIDalle // Default model
    @State private var isGeneratingImage: Bool = false
    @State private var generationError: String? = nil
    @State private var showGenerationErrorAlert: Bool = false

    // General error display
    @State private var showErrorAlert = false // For URL validation errors
    @State private var errorMessage = ""     // For URL validation errors

    // We might need a campaignId if images are associated with campaigns
    // For now, assuming it's not strictly required for this view or is handled by APIService if needed globally
    // @State var campaignId: Int? = nil // Example if needed


    private func isValidURL(_ urlString: String) -> Bool {
        if urlString.isEmpty { return false }
        if let url = URL(string: urlString), (url.scheme == "http" || url.scheme == "https") {
            return UIApplication.shared.canOpenURL(url)
        }
        return URL(string: urlString) != nil
    }

    private func addURL() {
        let trimmedURL = newImageURL.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedURL.isEmpty {
            errorMessage = "URL cannot be empty."
            showErrorAlert = true
            return
        }
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

    private func generateImage() {
        guard !imagePrompt.isEmpty else {
            generationError = "Image prompt cannot be empty."
            showGenerationErrorAlert = true
            return
        }

        isGeneratingImage = true
        generationError = nil

        // Assuming default size and quality for now, or they could be additional @State vars
        let params = ImageGenerationParams(
            prompt: imagePrompt,
            model: selectedModel,
            size: "1024x1024", // Example default, make this configurable if needed
            quality: selectedModel == .openAIDalle ? "standard" : nil, // DALL-E specific
            // campaignId: campaignId // Pass if campaignId is available and needed
            campaignId: nil // Not passing campaignId for now
        )

        Task {
            do {
                let response = try await apiService.generateImage(payload: params)
                if let newURL = response.imageUrl, !newURL.isEmpty {
                    if !imageURLs.contains(newURL) {
                        imageURLs.append(newURL)
                        print("[CharacterImageManagerView] Added new image URL: \(newURL). Current count: \(imageURLs.count)")
                    } else {
                        // Optionally inform user that this exact URL was already present
                        print("[CharacterImageManagerView] Generated image URL already exists in the list: \(newURL)")
                    }
                    imagePrompt = "" // Clear prompt on success
                } else {
                    generationError = "Image generation succeeded but returned no URL."
                    showGenerationErrorAlert = true
                }
            } catch {
                generationError = "Failed to generate image: \(error.localizedDescription)"
                showGenerationErrorAlert = true
            }
            isGeneratingImage = false
        }
    }


    var body: some View {
        NavigationView {
            Form { // Changed VStack to Form for better structure with sections
                Section(header: Text("AI Image Generation")) {
                    TextField("Enter image prompt", text: $imagePrompt)
                        .disabled(isGeneratingImage)

                    Picker("Select Model", selection: $selectedModel) {
                        ForEach(ImageModelName.allCases, id: \.self) { model in
                            Text(model.rawValue.capitalized).tag(model)
                        }
                    }
                    .disabled(isGeneratingImage)

                    Button(action: generateImage) {
                        HStack {
                            if isGeneratingImage {
                                ProgressView()
                                    .padding(.trailing, 4)
                                Text("Generating...")
                            } else {
                                Image(systemName: "sparkles")
                                Text("Generate Image")
                            }
                        }
                    }
                    .disabled(isGeneratingImage || imagePrompt.isEmpty)
                }
                .alert("Image Generation Error", isPresented: $showGenerationErrorAlert) {
                    Button("OK") { showGenerationErrorAlert = false }
                } message: {
                    Text(generationError ?? "An unknown error occurred.")
                }

                Section(header: Text("Add Image URL Manually")) {
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
                }
                .alert("URL Error", isPresented: $showErrorAlert) { // Changed title to be specific
                    Button("OK") { }
                } message: {
                    Text(errorMessage)
                }

                Section(header: Text("Current Images")) {
                    if imageURLs.isEmpty {
                        Text("No image URLs added yet. Add some above or generate one.")
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
