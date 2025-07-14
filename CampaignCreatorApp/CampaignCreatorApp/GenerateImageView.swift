import SwiftUI

struct GenerateImageView: View {
    @State private var prompt = ""
    @State private var isGenerating = false
    @State private var alertItem: AlertMessageItem?
    let onGenerateAIImage: ((String) async throws -> String)?
    let onImageGenerated: (String) -> Void
    @EnvironmentObject var imageUploadService: ImageUploadService
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("AI Image Prompt")) {
                    TextEditor(text: $prompt)
                        .frame(height: 100)
                }
                Button(action: {
                    Task {
                        await generateImage()
                    }
                }) {
                    HStack {
                        if isGenerating {
                            ProgressView().padding(.trailing, 4)
                            Text("Generating...")
                        } else {
                            Image(systemName: "sparkles")
                            Text("Generate Image")
                        }
                    }
                }
                .disabled(prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isGenerating)
            }
            .navigationTitle("Generate Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .alert(item: $alertItem) { item in
                Alert(title: Text("Image Generation Failed"), message: Text(item.message), dismissButton: .default(Text("OK")))
            }
        }
    }

    private func generateImage() async {
        guard let onGenerateAIImage = onGenerateAIImage else {
            return
        }

        isGenerating = true
        do {
            let newImageURL = try await onGenerateAIImage(prompt)
            onImageGenerated(newImageURL)
            dismiss()
        } catch {
            alertItem = AlertMessageItem(message: "Failed to generate AI image: \(error.localizedDescription)")
        }
        isGenerating = false
    }
}
