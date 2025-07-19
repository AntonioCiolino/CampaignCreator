import SwiftUI
import CampaignCreatorLib

struct CharacterImageManagerView: View {
    @StateObject private var viewModel: CharacterImageManagerViewModel

    @Environment(\.dismiss) var dismiss

    init(imageURLs: Binding<[String]>, characterID: Int) {
        _viewModel = StateObject(wrappedValue: CharacterImageManagerViewModel(imageURLs: imageURLs, characterID: characterID))
    }

    var body: some View {
        NavigationView {
            Form {
                aiImageGenerationSection
                addImageURLManuallySection
                currentImagesSection
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
                    if !viewModel.imageURLs.isEmpty { EditButton() }
                }
            }
            .alert("Error", isPresented: $viewModel.showErrorAlert) {
                Button("OK") { }
            } message: {
                Text(viewModel.errorMessage)
            }
        }
    }

    private var aiImageGenerationSection: some View {
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
        .alert("Image Generation Error", isPresented: $viewModel.showErrorAlert) {
            Button("OK") { viewModel.showErrorAlert = false }
        } message: {
            Text(viewModel.generationError ?? "An unknown error occurred.")
        }
    }

    private var addImageURLManuallySection: some View {
        Section(header: Text("Add Image URL Manually")) {
            HStack {
                TextField("Enter new image URL", text: $viewModel.newImageURL)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.none)
                    .keyboardType(.URL)
                Button(action: viewModel.addURL) {
                    Image(systemName: "plus.circle.fill")
                        .imageScale(.large)
                }
                .disabled(viewModel.newImageURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .alert("URL Error", isPresented: $viewModel.showErrorAlert) {
            Button("OK") { }
        } message: {
            Text(viewModel.errorMessage)
        }
    }

    private var currentImagesSection: some View {
        Section(header: Text("Current Images")) {
            if viewModel.imageURLs.isEmpty {
                Text("No image URLs added yet. Add some above or generate one.")
                    .foregroundColor(.secondary)
                    .padding(.vertical)
            } else {
                ForEach(viewModel.imageURLs, id: \.self) { urlString in
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
                        Spacer()
                    }
                }
                .onDelete(perform: viewModel.deleteURLs)
            }
        }
        .listStyle(InsetGroupedListStyle())
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
                CharacterImageManagerView(imageURLs: $urls, characterID: 1)
                CharacterImageManagerView(imageURLs: $emptyUrls, characterID: 2)
            }
        }
    }

    static var previews: some View {
        PreviewWrapper()
    }
}
