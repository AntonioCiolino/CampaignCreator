import SwiftUI
import CampaignCreatorLib
import Kingfisher

struct ErrorDetail: Decodable {
    let detail: String
}

struct CommonMoodBoardView: View {
    @Binding var imageURLs: [String]
    let onSave: () -> Void
    let onGenerateAIImage: ((String) async throws -> String)?
    let imageUploadService: ImageUploadService

    @State private var showingAddImageOptions = false
    @State private var showingAddURLSheet = false
    @State private var showingGenerateMoodboardImageSheet = false
    @State private var newImageURLInput: String = ""
    @State private var aiImagePromptInput: String = ""
    @State private var isGeneratingAIImage = false
    @State private var alertItem: AlertMessageItem?
    @Environment(\.editMode) private var editMode
    @State private var showingFullImageView = false
    @State private var selectedImageURL: URL?

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]

    var body: some View {
        ScrollView {
            if imageURLs.isEmpty {
                VStack {
                    Spacer()
                    Text("No images available.")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                LazyVGrid(columns: gridItemLayout, spacing: 2) {
                    ForEach(imageURLs, id: \.self) { urlString in
                        MoodboardCellView(
                            urlString: urlString,
                            onSelect: {
                                print("Selected image URL string: \(urlString)")
                                guard let url = URL(string: urlString) else {
                                    print("Failed to create URL from string: \(urlString)")
                                    alertItem = AlertMessageItem(message: "Invalid image URL.")
                                    return
                                }
                                selectedImageURL = url
                                showingFullImageView = true
                            },
                            onDelete: {
                                deleteImage(urlString: urlString)
                            }
                        )
                    }
                    .onMove(perform: moveImage)
                }
                .padding(2)
            }
        }
        .sheet(isPresented: $showingFullImageView) {
            FullCharacterImageViewWrapper(initialDisplayURL: selectedImageURL)
        }
        .navigationTitle("Mood Board")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                EditButton()
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showingAddImageOptions = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .confirmationDialog("Add Image", isPresented: $showingAddImageOptions, titleVisibility: .visible) {
            Button("Add from URL") {
                newImageURLInput = ""
                showingAddURLSheet = true
            }
            if onGenerateAIImage != nil {
                Button("Generate with AI") {
                    aiImagePromptInput = ""
                    showingGenerateMoodboardImageSheet = true
                }
            }
            Button("Cancel", role: .cancel) { }
        }
        .sheet(isPresented: $showingAddURLSheet) {
            addImageView
        }
        .sheet(isPresented: $showingGenerateMoodboardImageSheet) {
            generateMoodboardImageSheetView
        }
        .alert(item: $alertItem) { item in
            Alert(title: Text("Mood Board"), message: Text(item.message), dismissButton: .default(Text("OK")))
        }
    }

    private var addImageView: some View {
        NavigationView {
            Form {
                Section(header: Text("Image URL")) {
                    TextField("https://example.com/image.png", text: $newImageURLInput)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .textFieldStyle(.plain)
                }
                Button("Add Image") {
                    Task {
                        await addImageFromURL()
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

    private func addImageFromURL() async {
        let urlString = newImageURLInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: urlString) else {
            alertItem = AlertMessageItem(message: "Invalid URL provided.")
            return
        }

        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                alertItem = AlertMessageItem(message: "Failed to download image.")
                return
            }

            let filename = url.lastPathComponent
            let mimeType = response.mimeType ?? "application/octet-stream"
            let uploadResult = await imageUploadService.uploadImage(imageData: data, filename: filename, mimeType: mimeType)

            switch uploadResult {
            case .success(let newAzureURL):
                if !imageURLs.contains(newAzureURL) {
                    imageURLs.append(newAzureURL)
                    onSave()
                }
                showingAddURLSheet = false
            case .failure(let error):
                if case let .serverError(_, message) = error, let messageData = message?.data(using: .utf8) {
                    do {
                        let errorDetail = try JSONDecoder().decode(ErrorDetail.self, from: messageData)
                        alertItem = AlertMessageItem(message: "Failed to upload image: \(errorDetail.detail)")
                    } catch {
                        alertItem = AlertMessageItem(message: "Failed to upload image: \(error.localizedDescription)")
                    }
                } else {
                    alertItem = AlertMessageItem(message: "Failed to upload image: \(error.localizedDescription)")
                }
            }
        } catch {
            alertItem = AlertMessageItem(message: "Failed to download image: \(error.localizedDescription)")
        }
    }

    private var generateMoodboardImageSheetView: some View {
        NavigationView {
            Form {
                Section(header: Text("AI Image Prompt")) {
                    TextEditor(text: $aiImagePromptInput)
                        .frame(height: 100)
                }
                Button(action: {
                    Task {
                        await generateAndAddAIImage()
                    }
                }) {
                    HStack {
                        if isGeneratingAIImage {
                            ProgressView().padding(.trailing, 4)
                            Text("Generating...")
                        } else {
                            Image(systemName: "sparkles")
                            Text("Generate Image")
                        }
                    }
                }
                .disabled(aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isGeneratingAIImage)
            }
            .navigationTitle("Generate Image")
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

    private func generateAndAddAIImage() async {
        guard let onGenerateAIImage = onGenerateAIImage else {
            return
        }

        let prompt = aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else {
            alertItem = AlertMessageItem(message: "AI image prompt cannot be empty.")
            return
        }

        isGeneratingAIImage = true
        do {
            let newAzureURL = try await onGenerateAIImage(prompt)
            if !imageURLs.contains(newAzureURL) {
                imageURLs.append(newAzureURL)
                onSave()
            }
            showingGenerateMoodboardImageSheet = false
        } catch {
            alertItem = AlertMessageItem(message: "Failed to generate AI image: \(error.localizedDescription)")
        }
        isGeneratingAIImage = false
    }

    private func deleteImage(urlString: String) {
        imageURLs.removeAll { $0 == urlString }
        onSave()
    }

    private func moveImage(from source: IndexSet, to destination: Int) {
        imageURLs.move(fromOffsets: source, toOffset: destination)
        onSave()
    }

    private struct MoodboardCellView: View {
        let urlString: String
        let onSelect: () -> Void
        let onDelete: () -> Void
        @Environment(\.editMode) private var editMode

        private var isEditing: Bool {
            editMode?.wrappedValue.isEditing ?? false
        }

        var body: some View {
            ZStack(alignment: .topTrailing) {
                Button(action: onSelect) {
                    KFImage(URL(string: urlString))
                        .placeholder {
                            ProgressView()
                                .frame(maxWidth: .infinity, idealHeight: 120)
                                .background(Color.gray.opacity(0.1))
                        }
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(minWidth: 0, maxWidth: .infinity)
                        .frame(height: 120)
                        .clipped()
                }
                .buttonStyle(.plain)

                if isEditing {
                    Button(action: onDelete) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.red)
                            .background(Circle().fill(Color.white))
                            .padding(4)
                    }
                }
            }
        }
    }
}
