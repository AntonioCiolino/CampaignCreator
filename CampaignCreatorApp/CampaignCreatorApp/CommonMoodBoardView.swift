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

    let name: String

    init(imageURLs: Binding<[String]>, name: String, onSave: @escaping () -> Void, onGenerateAIImage: ((String) async throws -> String)?, imageUploadService: ImageUploadService, onSetBadge: ((String) -> Void)? = nil) {
        self.name = name
        _viewModel = StateObject(wrappedValue: CommonMoodBoardViewModel(imageURLs: imageURLs, onSave: onSave, onGenerateAIImage: onGenerateAIImage, imageUploadService: imageUploadService, onSetBadge: onSetBadge))
    }

    var body: some View {
        ScrollView {
            if viewModel.imageURLs.isEmpty {
                VStack {
                    Spacer()
                    Text("No images in \\(name)'s mood board yet.")
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
                                print("Selected image URL: \(urlString)")
                                selectedImageURL = URL(string: urlString)
                                showingFullImageView = true
                            },
                            onDelete: {
                                viewModel.deleteImage(urlString: urlString)
                            },
                            onSetBadge: {
                                viewModel.onSetBadge?(urlString)
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
            ImageGenerationView(isPresented: $viewModel.showingGenerateMoodboardImageSheet) { generatedImageURL in
                viewModel.imageURLs.append(generatedImageURL)
                viewModel.onSave()
            }
        }
        .alert(item: $viewModel.alertItem) { item in
            Alert(title: Text("Mood Board"), message: Text(item.message), dismissButton: .default(Text("OK")))
        }
    }

    private var addImageView: some View {
        NavigationView {
            Form {
                Section(header: Text("Image URL")) {
                    TextField("", text: $viewModel.newImageURLInput, prompt: Text("https://example.com/image.png").foregroundColor(.gray))
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

    private struct MoodboardCellView: View {
        let urlString: String
        let onSelect: () -> Void
        let onDelete: () -> Void
        let onSetBadge: () -> Void
        @Environment(\.editMode) private var editMode

        private var isEditing: Bool {
            editMode?.wrappedValue.isEditing ?? false
        }

        var body: some View {
            ZStack(alignment: .topTrailing) {
                KFImage(URL(string: urlString))
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(minWidth: 0, maxWidth: .infinity)
                    .frame(height: 120)
                    .clipped()
                    .contextMenu {
                        Button(action: onSelect) {
                            Text("View Image")
                            Image(systemName: "eye")
                        }
                        Button(action: onSetBadge) {
                            Text("Set as Badge")
                            Image(systemName: "star")
                        }
                    }

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
