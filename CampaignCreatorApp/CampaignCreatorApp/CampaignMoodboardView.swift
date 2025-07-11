import SwiftUI
import CampaignCreatorLib

struct CampaignMoodboardView: View {
    @State var localCampaign: Campaign // To allow modifications
    @ObservedObject var campaignCreator: CampaignCreator // For saving
    @EnvironmentObject var imageUploadService: ImageUploadService // Added for uploading external URLs

    // State for presenting sheets/dialogs
    @State private var showingAddImageOptions = false
    @State private var showingAddURLSheet = false
    @State private var showingGenerateMoodboardImageSheet = false
    @State private var newImageURLInput: String = "" // For URL input sheet
    @State private var aiImagePromptInput: String = "" // For AI generation sheet
    @State private var isGeneratingAIImage = false // For loading state of AI generation
    @State private var alertMessage: String? = nil // For showing alerts

    // Initializer to receive the campaign and campaignCreator
    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._localCampaign = State(initialValue: campaign)
        self.campaignCreator = campaignCreator
    }

    private var allImageURLs: [String] {
        var urls: [String] = []
        if let badge = localCampaign.badgeImageURL, !badge.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            urls.append(badge)
        }
        if let thematic = localCampaign.thematicImageURL, !thematic.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            urls.append(thematic)
        }
        if let moodboardImages = localCampaign.moodBoardImageURLs {
            urls.append(contentsOf: moodboardImages.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty })
        }
        // Remove duplicates, preserving order of first appearance
        var uniqueURLs = [String]()
        var seen = Set<String>()
        for url in urls {
            if !seen.contains(url) {
                uniqueURLs.append(url)
                seen.insert(url)
            }
        }
        return uniqueURLs
    }

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]

    @State private var selectedImageURLString: String? = nil
    // showingFullImageView will be managed by the NavigationLink or sheet presentation

    var body: some View {
        // This view will be pushed onto a navigation stack, so no NavigationView here.
        ScrollView {
            if allImageURLs.isEmpty {
                VStack {
                    Spacer()
                    Text("No images available for this campaign.")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                LazyVGrid(columns: gridItemLayout, spacing: 2) {
                    ForEach(allImageURLs, id: \.self) { urlString in
                        // let _ = print("[CampaignMoodboardView ForEach] Processing urlString for cell: \(urlString)")
                        CampaignMoodboardCellView(urlString: urlString)
                    }
                }
                .padding(2)
            }
        }
        .navigationTitle("\(localCampaign.title) Moodboard")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Save") {
                    Task {
                        await saveMoodboardChanges()
                    }
                }
            }
            ToolbarItem(placement: .navigationBarLeading) { // Changed to leading for +
                Button {
                    showingAddImageOptions = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .confirmationDialog("Add Image to Mood Board", isPresented: $showingAddImageOptions, titleVisibility: .visible) {
            Button("Add from URL") {
                newImageURLInput = "" // Clear previous input
                showingAddURLSheet = true
            }
            Button("Generate with AI") {
                aiImagePromptInput = "" // Clear previous input
                showingGenerateMoodboardImageSheet = true
            }
            Button("Cancel", role: .cancel) { }
        }
        // Sheets for adding URL and generating AI image will be added in subsequent steps
        .sheet(isPresented: $showingAddURLSheet) {
            addImageView
        }
        .sheet(isPresented: $showingGenerateMoodboardImageSheet) {
            generateMoodboardImageSheetView
        }
        .alert(item: $alertMessage) { message in // Alert for feedback
            Alert(title: Text("Mood Board Update"), message: Text(message), dismissButton: .default(Text("OK")))
        }
    }

    // View for adding an image via URL
    private var addImageView: some View {
        NavigationView {
            Form {
                Section(header: Text("Image URL")) {
                    TextField("https://example.com/image.png", text: $newImageURLInput)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                }
                Button("Add Image to Mood Board") {
                    Task {
                        await processAndAddExternalURL()
                    }
                }
                .disabled(newImageURLInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .navigationTitle("Add Image from URL")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        showingAddURLSheet = false
                    }
                }
            }
        }
    }

    private func processAndAddExternalURL() async {
        let urlString = newImageURLInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !urlString.isEmpty, let url = URL(string: urlString) else {
            self.alertMessage = "Invalid URL provided."
            return
        }

        // 1. Download image data from external URL
        do {
            print("[Moodboard] Downloading image from external URL: \(url)")
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                self.alertMessage = "Failed to download image. Status: \((response as? HTTPURLResponse)?.statusCode ?? -1)"
                return
            }

            // Determine filename and MIME type (best effort)
            let filename = url.lastPathComponent
            let mimeType = response.mimeType ?? "application/octet-stream"
            print("[Moodboard] Downloaded \(data.count) bytes. Filename: \(filename), MIME: \(mimeType)")

            // 2. Upload to our Azure Blob Storage via ImageUploadService
            let uploadResult = await imageUploadService.uploadImage(imageData: data, filename: filename, mimeType: mimeType)

            switch uploadResult {
            case .success(let newAzureURL):
                if localCampaign.moodBoardImageURLs == nil {
                    localCampaign.moodBoardImageURLs = []
                }
                if !localCampaign.moodBoardImageURLs!.contains(newAzureURL) {
                    localCampaign.moodBoardImageURLs!.append(newAzureURL)
                    self.alertMessage = "Image added to mood board! Remember to Save."
                    print("[Moodboard] Image uploaded to Azure and URL added to local mood board: \(newAzureURL)")
                } else {
                    self.alertMessage = "This image is already on the mood board."
                }
                showingAddURLSheet = false
                newImageURLInput = "" // Clear input
            case .failure(let error):
                self.alertMessage = "Failed to upload image to our storage: \(error.localizedDescription)"
                print("[Moodboard] Failed to upload image to Azure: \(error.localizedDescription)")
            }

        } catch {
            self.alertMessage = "Failed to download or process image from URL: \(error.localizedDescription)"
            print("[Moodboard] Error downloading image from URL: \(error.localizedDescription)")
        }
    }

    // View for generating an AI image for the mood board
    private var generateMoodboardImageSheetView: some View {
        NavigationView {
            Form {
                Section(header: Text("AI Image Prompt")) {
                    TextEditor(text: $aiImagePromptInput)
                        .frame(height: 100)
                }
                Button(action: {
                    Task {
                        await performAIMoodboardImageGeneration()
                    }
                }) {
                    HStack {
                        if isGeneratingAIImage {
                            ProgressView().padding(.trailing, 4)
                            Text("Generating...")
                        } else {
                            Image(systemName: "sparkles")
                            Text("Generate Image for Mood Board")
                        }
                    }
                }
                .disabled(aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isGeneratingAIImage)
            }
            .navigationTitle("Generate Mood Board Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        showingGenerateMoodboardImageSheet = false
                    }
                }
            }
        }
    }

    private func performAIMoodboardImageGeneration() async {
        let prompt = aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else {
            self.alertMessage = "AI image prompt cannot be empty."
            return
        }

        isGeneratingAIImage = true
        // Assuming campaignCreator.generateImage handles errors by throwing
        // and returns an ImageGenerationResponse with an imageUrl.
        do {
            let response = try await campaignCreator.generateImage(
                prompt: prompt,
                modelName: ImageModelName.defaultOpenAI.rawValue, // Or make this selectable
                associatedCampaignId: String(localCampaign.id) // Associate with campaign for context/storage path
            )

            if let newAzureURL = response.imageUrl {
                if localCampaign.moodBoardImageURLs == nil {
                    localCampaign.moodBoardImageURLs = []
                }
                if !localCampaign.moodBoardImageURLs!.contains(newAzureURL) {
                    localCampaign.moodBoardImageURLs!.append(newAzureURL)
                    self.alertMessage = "AI Image generated and added to mood board! Remember to Save."
                    print("[Moodboard] AI Image generated and URL added to local mood board: \(newAzureURL)")
                } else {
                    self.alertMessage = "This AI generated image (or one with the same URL) is already on the mood board."
                }
                aiImagePromptInput = "" // Clear prompt
            } else {
                self.alertMessage = "AI image generation succeeded but returned no URL."
            }
        } catch {
            self.alertMessage = "Failed to generate AI image: \(error.localizedDescription)"
            print("[Moodboard] Failed to generate AI image: \(error.localizedDescription)")
        }
        isGeneratingAIImage = false
        showingGenerateMoodboardImageSheet = false // Dismiss sheet
    }

    private func saveMoodboardChanges() async {
        print("[CampaignMoodboardView] Attempting to save moodboard changes for campaign ID: \(localCampaign.id)")
        do {
            // The campaignCreator.updateCampaign expects the full campaign object.
            // localCampaign already has the modifications to moodBoardImageURLs.
            // Make sure markAsModified is called if not done automatically by @State changes triggering this save.
            localCampaign.markAsModified() // Ensure modifiedAt is updated
            _ = try await campaignCreator.updateCampaign(localCampaign)
            print("[CampaignMoodboardView] Successfully saved campaign with updated moodboard.")
            // Optionally, provide user feedback like an alert or toast.
            // Consider if the parent view (CampaignDetailView) needs to be explicitly refreshed.
            // If CampaignDetailView's campaign object is not a @Binding or @ObservedObject
            // that reflects changes from CampaignCreator's list, it might show stale data
            // until it's reloaded or refreshed by other means.
            // For now, assuming CampaignCreator's update to its `campaigns` list will eventually propagate.
        } catch {
            print("❌ [CampaignMoodboardView] Error saving moodboard changes: \(error.localizedDescription)")
            // TODO: Show error to user
        }
    }

    // Private helper view for each cell in the campaign moodboard grid
    private struct CampaignMoodboardCellView: View {
        let urlString: String

        var body: some View {
            // NavigationLink to FullCharacterImageView (which is generic enough for any image URL)
            let destinationURL = URL(string: urlString)
            NavigationLink(destination: FullCharacterImageViewWrapper(initialDisplayURL: destinationURL)
                            .navigationTitle("Image Detail")
                            .navigationBarTitleDisplayMode(.inline)
            ) {
                AsyncImage(url: URL(string: urlString)) { phase in
                    switch phase {
                    case .empty:
                        ProgressView()
                            .frame(maxWidth: .infinity, idealHeight: 120)
                            .background(Color.gray.opacity(0.1))
                    case .success(let image):
                        image.resizable()
                            .aspectRatio(contentMode: .fill)
                            .frame(minWidth: 0, maxWidth: .infinity)
                            .frame(height: 120)
                            .clipped()
                    case .failure:
                        Image(systemName: "photo.fill")
                            .resizable()
                            .scaledToFit()
                            .frame(width: 50, height: 50)
                            .foregroundColor(.gray)
                            .frame(maxWidth: .infinity, idealHeight: 120)
                            .background(Color.gray.opacity(0.1))
                    @unknown default:
                        EmptyView()
                    }
                }
            }
            .buttonStyle(.plain)
        }
    }
}

struct CampaignMoodboardView_Previews: PreviewProvider {
    static var previews: some View {
        let sampleCampaignWithImages = Campaign(
            id: 1,
            title: "Test Campaign",
            sections: [], // sections comes before badgeImageURL
            badgeImageURL: "https://picsum.photos/seed/badge/200/200",
            thematicImageURL: "https://picsum.photos/seed/thematic/600/400",
            moodBoardImageURLs: [
                "https://picsum.photos/seed/mb1/300/300",
                "https://picsum.photos/seed/mb2/300/300",
                "http://example.com/invalid.jpg"
            ]
            // other parameters will use their defaults
        )

        let sampleCampaignNoImages = Campaign(
            id: 2,
            title: "Empty Campaign",
            sections: []
        )

        Group {
            NavigationView {
                CampaignMoodboardView(campaign: sampleCampaignWithImages)
            }
            .previewDisplayName("With Images")

            NavigationView {
                CampaignMoodboardView(campaign: sampleCampaignNoImages)
            }
            .previewDisplayName("No Images")
        }
    }
}
