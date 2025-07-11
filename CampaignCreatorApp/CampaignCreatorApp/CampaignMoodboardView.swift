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
    @State private var alertItem: AlertMessageItem? = nil // Changed for Identifiable alert

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
        .alert(item: $alertItem) { item in // Use alertItem and access its message
            Alert(title: Text("Mood Board Update"), message: Text(item.message), dismissButton: .default(Text("OK")))
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
        print("[Moodboard AddURL] processAndAddExternalURL started.")
        let urlString = newImageURLInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !urlString.isEmpty, let url = URL(string: urlString) else {
            print("[Moodboard AddURL] Invalid URL: \(urlString)")
            self.alertItem = AlertMessageItem(message: "Invalid URL provided.")
            return
        }
        print("[Moodboard AddURL] URL validated: \(url)")

        // 1. Download image data from external URL
        do {
            print("[Moodboard AddURL] Downloading image from external URL: \(url)")
            let (data, response) = try await URLSession.shared.data(from: url)
            print("[Moodboard AddURL] Download response received.")
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                print("[Moodboard AddURL] Failed to download image. Status: \((response as? HTTPURLResponse)?.statusCode ?? -1)")
                self.alertItem = AlertMessageItem(message: "Failed to download image. Status: \((response as? HTTPURLResponse)?.statusCode ?? -1)")
                return
            }
            print("[Moodboard AddURL] Image data downloaded successfully (\(data.count) bytes).")

            // Determine filename and MIME type (best effort)
            let filename = url.lastPathComponent
            let mimeType = response.mimeType ?? "application/octet-stream"
            print("[Moodboard AddURL] Filename: \(filename), MIME: \(mimeType)")

            // 2. Upload to our Azure Blob Storage via ImageUploadService
            print("[Moodboard AddURL] Attempting to upload to ImageUploadService.")
            let uploadResult = await imageUploadService.uploadImage(imageData: data, filename: filename, mimeType: mimeType)
            print("[Moodboard AddURL] ImageUploadService result: \(uploadResult)")

            switch uploadResult {
            case .success(let newAzureURL):
                print("[Moodboard AddURL] Upload success. New Azure URL: \(newAzureURL)")
                if localCampaign.moodBoardImageURLs == nil {
                    localCampaign.moodBoardImageURLs = []
                    print("[Moodboard AddURL] Initialized moodBoardImageURLs.")
                }
                if !localCampaign.moodBoardImageURLs!.contains(newAzureURL) {
                    localCampaign.moodBoardImageURLs!.append(newAzureURL)
                    self.alertItem = AlertMessageItem(message: "Image added to mood board! Remember to Save.")
                    print("[Moodboard AddURL] Image URL appended to localCampaign.moodBoardImageURLs.")
                } else {
                    self.alertItem = AlertMessageItem(message: "This image is already on the mood board.")
                    print("[Moodboard AddURL] Image already in moodboard.")
                }
                newImageURLInput = "" // Clear input
                print("[Moodboard AddURL] Setting showingAddURLSheet = false")
                showingAddURLSheet = false // This should dismiss the sheet
            case .failure(let error):
                self.alertItem = AlertMessageItem(message: "Failed to upload image to our storage: \(error.localizedDescription)")
                print("[Moodboard AddURL] Failed to upload image to Azure: \(error.localizedDescription)")
                // Ensure sheet is dismissed even on failure if that's desired, or keep it open.
                // For now, let's assume we want to dismiss it.
                print("[Moodboard AddURL] Setting showingAddURLSheet = false (on failure)")
                showingAddURLSheet = false
            }

        } catch {
            self.alertItem = AlertMessageItem(message: "Failed to download or process image from URL: \(error.localizedDescription)")
            print("[Moodboard AddURL] Error downloading image from URL: \(error.localizedDescription)")
            print("[Moodboard AddURL] Setting showingAddURLSheet = false (on catch)")
            showingAddURLSheet = false
        }
        print("[Moodboard AddURL] processAndAddExternalURL finished.")
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
        print("[Moodboard AI Gen] Started.")
        let prompt = aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else {
            self.alertItem = AlertMessageItem(message: "AI image prompt cannot be empty.")
            print("[Moodboard AI Gen] Prompt was empty.")
            return
        }

        isGeneratingAIImage = true
        print("[Moodboard AI Gen] Calling campaignCreator.generateImage with prompt: \(prompt)")
        do {
            let response = try await campaignCreator.generateImage(
                prompt: prompt,
                modelName: ImageModelName.defaultOpenAI.rawValue,
                associatedCampaignId: String(localCampaign.id)
            )
            print("[Moodboard AI Gen] campaignCreator.generateImage response received. Image URL: \(response.imageUrl ?? "nil")")

            if let newAzureURL = response.imageUrl, !newAzureURL.isEmpty {
                if localCampaign.moodBoardImageURLs == nil {
                    localCampaign.moodBoardImageURLs = []
                    print("[Moodboard AI Gen] Initialized moodBoardImageURLs.")
                }
                if !localCampaign.moodBoardImageURLs!.contains(newAzureURL) {
                    localCampaign.moodBoardImageURLs!.append(newAzureURL)
                    self.alertItem = AlertMessageItem(message: "AI Image generated and added to mood board! Remember to Save.")
                    print("[Moodboard AI Gen] Image URL appended. New moodboard URLs: \(localCampaign.moodBoardImageURLs!)")
                } else {
                    self.alertItem = AlertMessageItem(message: "This AI generated image (or one with the same URL) is already on the mood board.")
                    print("[Moodboard AI Gen] URL already in moodboard.")
                }
                aiImagePromptInput = ""
            } else {
                self.alertItem = AlertMessageItem(message: "AI image generation succeeded but returned no URL.")
                print("[Moodboard AI Gen] Generated image URL was nil or empty from service.")
            }
        } catch {
            self.alertItem = AlertMessageItem(message: "Failed to generate AI image: \(error.localizedDescription)")
            print("[Moodboard AI Gen] Error during AI image generation: \(error.localizedDescription)")
        }
        isGeneratingAIImage = false
        showingGenerateMoodboardImageSheet = false
        print("[Moodboard AI Gen] Finished. Dismissing sheet.")
    }

    private func saveMoodboardChanges() async {
        print("[CMV SaveChanges] Attempting to save moodboard for campaign ID: \(localCampaign.id)")
        print("[CMV SaveChanges] Current localCampaign.moodBoardImageURLs before save: \(localCampaign.moodBoardImageURLs ?? [])")
        do {
            localCampaign.markAsModified()
            print("[CMV SaveChanges] Calling campaignCreator.updateCampaign...")
            let updatedCampaign = try await campaignCreator.updateCampaign(localCampaign)
            print("[CMV SaveChanges] Successfully called campaignCreator.updateCampaign. Response moodboard URLs: \(updatedCampaign.moodBoardImageURLs ?? [])")
            // Update localCampaign with the version from the server to ensure consistency,
            // especially for modifiedAt and any other server-side changes.
            self.localCampaign = updatedCampaign
            self.alertItem = AlertMessageItem(message: "Moodboard changes saved successfully!")
        } catch {
            print("❌ [CMV SaveChanges] Error saving moodboard changes: \(error.localizedDescription)")
            self.alertItem = AlertMessageItem(message: "Failed to save moodboard: \(error.localizedDescription)")
        }
    }

    // Private helper view for each cell in the campaign moodboard grid
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

        // Create mock/dummy instances for preview
        let mockApiService = APIService()
        let mockCampaignCreator = CampaignCreator(apiService: mockApiService)
        let mockImageUploadService = ImageUploadService(apiService: mockApiService)

        Group {
            NavigationView {
                CampaignMoodboardView(campaign: sampleCampaignWithImages, campaignCreator: mockCampaignCreator)
                    .environmentObject(mockCampaignCreator)
                    .environmentObject(mockImageUploadService)
            }
            .previewDisplayName("With Images")

            NavigationView {
                CampaignMoodboardView(campaign: sampleCampaignNoImages, campaignCreator: mockCampaignCreator)
                    .environmentObject(mockCampaignCreator)
                    .environmentObject(mockImageUploadService)
            }
            .previewDisplayName("No Images")
        }
    }
}
