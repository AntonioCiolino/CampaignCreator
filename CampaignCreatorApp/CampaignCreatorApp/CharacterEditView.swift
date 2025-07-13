import SwiftUI
import CampaignCreatorLib

struct CharacterEditView: View {
    @StateObject private var viewModel: CharacterEditViewModel
    @Binding var isPresented: Bool
    var onCharacterUpdated: ((Character) -> Void)?

    @Environment(\.dismiss) var dismiss

    init(character: Character, isPresented: Binding<Bool>, onCharacterUpdated: ((Character) -> Void)? = nil) {
        _viewModel = StateObject(wrappedValue: CharacterEditViewModel(character: character))
        _isPresented = isPresented
        self.onCharacterUpdated = onCharacterUpdated
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Basic Information")) {
                    TextField("Name*", text: $viewModel.name)
                }

                Section(header: Text("Statistics (Optional)")) {
                    StatEditableRow(label: "Strength", valueString: $viewModel.statsStrength)
                    StatEditableRow(label: "Dexterity", valueString: $viewModel.statsDexterity)
                    StatEditableRow(label: "Constitution", valueString: $viewModel.statsConstitution)
                    StatEditableRow(label: "Intelligence", valueString: $viewModel.statsIntelligence)
                    StatEditableRow(label: "Wisdom", valueString: $viewModel.statsWisdom)
                    StatEditableRow(label: "Charisma", valueString: $viewModel.statsCharisma)
                }

                Section(header: Text("Narrative Details")) {
                    DisclosureGroup("Description", isExpanded: $viewModel.isDescriptionExpanded) {
                        VStack(alignment: .leading) {
                            TextEditor(text: $viewModel.descriptionText)
                                .frame(height: 100)
                                .overlay(formElementOverlay())
                            Button(action: { Task { await viewModel.generateAspect(forField: .description) } }) {
                                Label("Generate Description", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderless)
                            .disabled(viewModel.isGenerating)
                        }
                    }

                    DisclosureGroup("Appearance", isExpanded: $viewModel.isAppearanceExpanded) {
                        VStack(alignment: .leading) {
                            TextEditor(text: $viewModel.appearanceDescriptionText)
                                .frame(height: 100)
                                .overlay(formElementOverlay())
                            Button(action: { Task { await viewModel.generateAspect(forField: .appearance) } }) {
                                Label("Generate Appearance", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderless)
                            .disabled(viewModel.isGenerating)
                        }
                    }
                }

                Section(header: Text("Character Images")) {
                    if viewModel.imageURLsText.isEmpty {
                        Text("No images. Manage images to add or generate new ones.")
                            .foregroundColor(.secondary)
                            .padding(.vertical)
                    } else {
                        TabView {
                            ForEach(viewModel.imageURLsText, id: \.self) { urlString in
                                if let url = URL(string: urlString) {
                                    AsyncImage(url: url) { phase in
                                        switch phase {
                                        case .empty:
                                            ProgressView()
                                        case .success(let image):
                                            image.resizable()
                                                .aspectRatio(contentMode: .fit)
                                        case .failure:
                                            Image(systemName: "photo.fill")
                                                .foregroundColor(.gray)
                                                .overlay(Text("Error").font(.caption).foregroundColor(.red))
                                        @unknown default:
                                            EmptyView()
                                        }
                                    }
                                    .frame(height: 200)
                                    .clipped()
                                } else {
                                    Image(systemName: "photo.fill")
                                        .foregroundColor(.gray)
                                        .overlay(Text("Invalid URL").font(.caption).foregroundColor(.red))
                                        .frame(height: 200)
                                }
                            }
                        }
                        .tabViewStyle(PageTabViewStyle())
                        .frame(height: 220)
                    }

                    Button(action: {
                        viewModel.showingImageManager = true
                    }) {
                        Label("Manage Images", systemImage: "photo.on.rectangle.angled")
                    }
                }

                Section(header: Text("Additional Information")) {
                    VStack(alignment: .leading) {
                        Text("Notes for LLM (Optional)").font(.caption).foregroundColor(.gray)
                        TextEditor(text: $viewModel.notesForLLMText).frame(height: 80)
                            .overlay(formElementOverlay())
                    }
                    Picker("Export Format Preference", selection: $viewModel.selectedExportFormat) {
                        ForEach(CharacterEditViewModel.ExportFormat.allCases) { format in
                            Text(format.displayName).tag(format)
                        }
                    }
                }

                if let error = viewModel.errorMessage {
                    Text("Error: \\(error)").foregroundColor(.red).font(.caption)
                }
            }
            .navigationTitle("Edit Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }.disabled(viewModel.isSaving || viewModel.isGenerating)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if viewModel.isSaving || viewModel.isGenerating {
                        ProgressView()
                    } else {
                        Button("Save") {
                            Task {
                                let updatedCharacter = await viewModel.saveCharacterChanges()
                                if let updatedCharacter = updatedCharacter {
                                    onCharacterUpdated?(updatedCharacter)
                                    dismiss()
                                }
                            }
                        }
                        .disabled(viewModel.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSaving || viewModel.isGenerating)
                    }
                }
            }
            .alert("Error Updating Character", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: { Text(viewModel.errorMessage ?? "") }
            .disabled(viewModel.isSaving || viewModel.isGenerating)
            .sheet(isPresented: $viewModel.showingImageManager) {
                CharacterImageManagerView(imageURLs: $viewModel.imageURLsText, characterID: viewModel.characterToEdit.id)
            }
        }
    }

    private func formElementOverlay() -> some View {
        RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1)
    }
}

struct StatEditableRow: View.swift
    let label: String
    @Binding var valueString: String
    var body: some View {
        HStack {
            Text(label)
            Spacer()
            TextField("0", text: $valueString)
                .keyboardType(.numberPad).frame(width: 50)
                .multilineTextAlignment(.trailing).textFieldStyle(RoundedBorderTextFieldStyle())
        }
    }
}

struct CharacterEditView_Previews: PreviewProvider {
    static var previews: some View {
        // Use a static property wrapper for the binding
        @State var isPresented: Bool = true

        // Create a mock library character stats first
        let libStats = CampaignCreatorLib.CharacterStats(
            strength: 10,
            dexterity: 15,
            constitution: 12,
            intelligence: 11,
            wisdom: 13,
            charisma: 14
        )

        // Create a mock library character
        let libCharacter = CampaignCreatorLib.Character(
            id: 1,
            name: "Aella Swiftarrow (Edit)",
            description: "A nimble scout...",
            appearanceDescription: "Slender build...",
            imageURLs: ["http://example.com/img1.png"],
            notesForLLM: "Loves nature.",
            stats: libStats,
            exportFormatPreference: "Markdown",
            ownerID: 1,
            campaignIDs: []
        )

        // Use the failable initializer to create the app-level character
        let sampleCharacter = Character(from: libCharacter)!

        return CharacterEditView(
            character: sampleCharacter,
            isPresented: $isPresented
        )
    }
}
