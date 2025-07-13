import SwiftUI

struct CharacterCreateView: View {
    @StateObject private var viewModel = CharacterCreateViewModel()
    @Binding var isPresented: Bool

    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Character Details")) {
                    TextField("Name*", text: $viewModel.characterName)
                        .disabled(viewModel.isSaving || viewModel.isGenerating)
                    generateableTextField(title: "Description", text: $viewModel.characterDescription, fieldType: .description, isGenerating: $viewModel.isGenerating)
                    generateableTextField(title: "Appearance", text: $viewModel.characterAppearance, fieldType: .appearance, isGenerating: $viewModel.isGenerating)
                }

                Section(header: Text("Image URLs")) {
                    ForEach(viewModel.characterImageURLsText.indices, id: \.self) { index in
                        HStack {
                            TextField("Image URL", text: $viewModel.characterImageURLsText[index])
                            Button(action: { viewModel.characterImageURLsText.remove(at: index) }) {
                                Image(systemName: "trash").foregroundColor(.red)
                            }
                        }
                    }
                    HStack {
                        TextField("Add new image URL", text: $viewModel.newImageURL)
                        Button(action: {
                            if !viewModel.newImageURL.isEmpty, let _ = URL(string: viewModel.newImageURL) {
                                viewModel.characterImageURLsText.append(viewModel.newImageURL)
                                viewModel.newImageURL = ""
                            }
                        }) {
                            Image(systemName: "plus.circle.fill")
                        }
                        .disabled(viewModel.newImageURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }

                Section(header: Text("Additional Information")) {
                    VStack(alignment: .leading) {
                        Text("Notes for LLM (Optional)").font(.caption).foregroundColor(.gray)
                        TextEditor(text: $viewModel.characterNotesForLLM)
                            .frame(height: 80)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                            .disabled(viewModel.isSaving || viewModel.isGenerating)
                    }
                    TextField("Export Format Preference", text: $viewModel.characterExportFormatPreference)
                        .disabled(viewModel.isSaving || viewModel.isGenerating)
                }

                if let error = viewModel.errorMessage {
                    Section {
                        Text("Error: \\(error)").foregroundColor(.red).font(.caption)
                    }
                }
            }
            .navigationTitle("New Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .disabled(viewModel.isSaving || viewModel.isGenerating)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if viewModel.isSaving || viewModel.isGenerating {
                        ProgressView()
                    } else {
                        Button("Save") {
                            Task {
                                await viewModel.saveCharacter()
                                if viewModel.errorMessage == nil {
                                    dismiss()
                                }
                            }
                        }
                        .disabled(viewModel.characterName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSaving)
                    }
                }
            }
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "An unknown error occurred.")
            }
        }
    }

    @ViewBuilder
    private func generateableTextField(title: String, text: Binding<String>, fieldType: CharacterCreateViewModel.AspectField, isGenerating: Binding<Bool>) -> some View {
        VStack(alignment: .leading) {
            HStack {
                Text(title).font(.caption).foregroundColor(.gray)
                Spacer()
                Button(action: { Task { await viewModel.generateAspect(forField: fieldType) } }) {
                    Label("Generate", systemImage: "sparkles")
                }
                .buttonStyle(.borderless)
                .disabled(viewModel.isGenerating || viewModel.characterName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            TextEditor(text: text)
                .frame(height: 100)
                .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                .disabled(viewModel.isGenerating)
        }
    }
}

struct CharacterCreateView_Previews: PreviewProvider {
    static var previews: some View {
        @State var isPresented: Bool = true
        CharacterCreateView(isPresented: $isPresented)
    }
}
