import SwiftUI
import Kingfisher

struct ErrorDetail: Decodable {
    let detail: String
}

struct CommonMoodBoardView: View {
    @StateObject private var viewModel: CommonMoodBoardViewModel
    @Environment(\.editMode) private var editMode
    @State private var showingFullImageView = false
    @State private var selectedImageURL: URL?

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]

    init(imageURLs: Binding<[String]>, onSave: @escaping () -> Void, onGenerateAIImage: ((String) async throws -> String)?, imageUploadService: ImageUploadService) {
        _viewModel = StateObject(wrappedValue: CommonMoodBoardViewModel(imageURLs: imageURLs, onSave: onSave, onGenerateAIImage: onGenerateAIImage, imageUploadService: imageUploadService))
    }

    var body: some View {
        ScrollView {
            if viewModel.imageURLs.isEmpty {
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
                    ForEach(viewModel.imageURLs, id: \.self) { urlString in
                        MoodboardCellView(
                            urlString: urlString,
                            onSelect: {
                                selectedImageURL = URL(string: urlString)
                                showingFullImageView = true
                            },
                            onDelete: {
                                viewModel.deleteImage(urlString: urlString)
                            }
                        )
                    }
                    .onMove(perform: viewModel.moveImage)
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
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    viewModel.showingAddImageOptions = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .confirmationDialog("Add Image", isPresented: $viewModel.showingAddImageOptions, titleVisibility: .visible) {
            Button("Add from URL") {
                viewModel.newImageURLInput = ""
                viewModel.showingAddURLSheet = true
            }
            if viewModel.onGenerateAIImage != nil {
                Button("Generate with AI") {
                    viewModel.aiImagePromptInput = ""
                    viewModel.showingGenerateMoodboardImageSheet = true
                }
            }
            Button("Cancel", role: .cancel) { }
        }
        .sheet(isPresented: $viewModel.showingAddURLSheet) {
            addImageView
        }
        .sheet(isPresented: $viewModel.showingGenerateMoodboardImageSheet) {
            generateMoodboardImageSheetView
        }
        .alert(item: $viewModel.alertItem) { item in
            Alert(title: Text("Mood Board"), message: Text(item.message), dismissButton: .default(Text("OK")))
        }
    }

    private var addImageView: some View {
        NavigationView {
            Form {
                Section(header: Text("Image URL")) {
                    TextField("https://example.com/image.png", text: $viewModel.newImageURLInput)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .textFieldStyle(.plain)
                }
                Button("Add Image") {
                    Task {
                        await viewModel.addImageFromURL()
                    }
                }
                .disabled(viewModel.newImageURLInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .navigationTitle("Add Image from URL")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        viewModel.showingAddURLSheet = false
                    }
                }
            }
        }
    }

    private var generateMoodboardImageSheetView: some View {
        NavigationView {
            Form {
                Section(header: Text("AI Image Prompt")) {
                    TextEditor(text: $viewModel.aiImagePromptInput)
                        .frame(height: 100)
                }
                Button(action: {
                    Task {
                        await viewModel.generateAndAddAIImage()
                    }
                }) {
                    HStack {
                        if viewModel.isGeneratingAIImage {
                            ProgressView().padding(.trailing, 4)
                            Text("Generating...")
                        } else {
                            Image(systemName: "sparkles")
                            Text("Generate Image")
                        }
                    }
                }
                .disabled(viewModel.aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isGeneratingAIImage)
            }
            .navigationTitle("Generate Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        viewModel.showingGenerateMoodboardImageSheet = false
                    }
                }
            }
        }
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
                    if let url = URL(string: urlString), url.isFileURL {
                        if let imageData = try? Data(contentsOf: url), let uiImage = UIImage(data: imageData) {
                            Image(uiImage: uiImage)
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                                .frame(minWidth: 0, maxWidth: .infinity)
                                .frame(height: 120)
                                .clipped()
                        } else {
                            Image(systemName: "photo")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 40, height: 40)
                                .foregroundColor(.gray)
                        }
                    } else {
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
