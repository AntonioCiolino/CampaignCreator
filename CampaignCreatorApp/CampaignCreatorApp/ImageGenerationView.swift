import SwiftUI
import CampaignCreatorLib

struct ImageGenerationView: View {
    @StateObject private var viewModel: ImageManagerViewModel
    @Binding var isPresented: Bool
    var onImageGenerated: (String) -> Void

    init(isPresented: Binding<Bool>, onImageGenerated: @escaping (String) -> Void) {
        _isPresented = isPresented
        self.onImageGenerated = onImageGenerated
        _viewModel = StateObject(wrappedValue: ImageManagerViewModel(imageURLs: .constant([])))
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("AI Image Generation")) {
                    TextField("Enter image prompt", text: $viewModel.imagePrompt)
                        .disabled(viewModel.isGeneratingImage)

                    Picker("Select Model", selection: $viewModel.selectedModel) {
                        ForEach(CampaignCreatorLib.ImageModelName.allCases, id: \.self) { model in
                            Text(model.rawValue.capitalized).tag(model)
                        }
                    }
                    .disabled(viewModel.isGeneratingImage)

                    Button(action: viewModel.generateImage) {
                        HStack {
                            Image(systemName: "sparkles")
                            Text("Generate Image")
                        }
                    }
                    .disabled(viewModel.isGeneratingImage || viewModel.imagePrompt.isEmpty)

                    if viewModel.isGeneratingImage {
                        HStack {
                            ProgressView()
                                .padding(.trailing, 4)
                            Text(viewModel.generationStatus)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }

                if let generatedImageURL = viewModel.imageURLs.first {
                    Section(header: Text("Generated Image")) {
                        AsyncImage(url: URL(string: generatedImageURL)) { phase in
                            switch phase {
                            case .empty:
                                ProgressView()
                            case .success(let image):
                                image.resizable()
                                    .aspectRatio(contentMode: .fit)
                            case .failure:
                                Image(systemName: "photo.fill")
                                    .foregroundColor(.gray)
                            @unknown default:
                                EmptyView()
                            }
                        }
                        .frame(height: 200)
                        .clipped()

                        Button("Accept") {
                            onImageGenerated(generatedImageURL)
                            isPresented = false
                        }
                    }
                }
            }
            .navigationTitle("Generate Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        isPresented = false
                    }
                }
            }
            .alert("Image Generation Error", isPresented: $viewModel.showErrorAlert) {
                Button("OK") { }
            } message: {
                Text(viewModel.generationError ?? "An unknown error occurred.")
            }
        }
    }
}
