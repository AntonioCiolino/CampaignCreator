import SwiftUI
import SwiftData

struct CharacterEditView: View {
    @Bindable var character: Character
    @Binding var isPresented: Bool

    @State private var isDescriptionExpanded: Bool = true
    @State private var isAppearanceExpanded: Bool = true
    @State private var showingImageManager = false

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Basic Information")) {
                    TextField("Name*", text: $character.name)
                }

                Section(header: Text("Statistics (Optional)")) {
                    StatEditableRow(label: "Strength", value: $character.stats?.strength)
                    StatEditableRow(label: "Dexterity", value: $character.stats?.dexterity)
                    StatEditableRow(label: "Constitution", value: $character.stats?.constitution)
                    StatEditableRow(label: "Intelligence", value: $character.stats?.intelligence)
                    StatEditableRow(label: "Wisdom", value: $character.stats?.wisdom)
                    StatEditableRow(label: "Charisma", value: $character.stats?.charisma)
                }

                Section(header: Text("Narrative Details")) {
                    DisclosureGroup("Description", isExpanded: $isDescriptionExpanded) {
                        VStack(alignment: .leading) {
                            TextEditor(text: .init(get: { character.character_description ?? "" }, set: { character.character_description = $0 }))
                                .frame(height: 100)
                                .overlay(formElementOverlay())
                        }
                    }

                    DisclosureGroup("Appearance", isExpanded: $isAppearanceExpanded) {
                        VStack(alignment: .leading) {
                            TextEditor(text: .init(get: { character.appearance_description ?? "" }, set: { character.appearance_description = $0 }))
                                .frame(height: 100)
                                .overlay(formElementOverlay())
                        }
                    }
                }

                Section(header: Text("Character Images")) {
                    if (character.image_urls ?? []).isEmpty {
                        Text("No images. Manage images to add or generate new ones.")
                            .foregroundColor(.secondary)
                            .padding(.vertical)
                    } else {
                        TabView {
                            ForEach(character.image_urls ?? [], id: \.self) { urlString in
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
                        showingImageManager = true
                    }) {
                        Label("Manage Images", systemImage: "photo.on.rectangle.angled")
                    }
                }

                Section(header: Text("Additional Information")) {
                    VStack(alignment: .leading) {
                        Text("Notes for LLM (Optional)").font(.caption).foregroundColor(.gray)
                        TextEditor(text: .init(get: { character.notes_for_llm ?? "" }, set: { character.notes_for_llm = $0 })).frame(height: 80)
                            .overlay(formElementOverlay())
                    }
                    Picker("Export Format Preference", selection: .init(get: { character.export_format_preference ?? "Complex" }, set: { character.export_format_preference = $0 })) {
                        Text("Complex").tag("Complex")
                        Text("Simple").tag("Simple")
                    }
                }
            }
            .navigationTitle("Edit Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { isPresented = false }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        isPresented = false
                    }
                    .disabled(character.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
            .sheet(isPresented: $showingImageManager) {
                CharacterImageManagerView(imageURLs: .init(get: { character.image_urls ?? [] }, set: { character.image_urls = $0 }), characterID: 0)
            }
        }
    }

    private func formElementOverlay() -> some View {
        RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1)
    }
}

struct StatEditableRow: View {
    let label: String
    @Binding var value: Int?

    @State private var valueString: String = ""

    var body: some View {
        HStack {
            Text(label)
            Spacer()
            TextField("0", text: $valueString)
                .keyboardType(.numberPad).frame(width: 50)
                .multilineTextAlignment(.trailing).textFieldStyle(RoundedBorderTextFieldStyle())
                .onAppear {
                    valueString = value.map(String.init) ?? ""
                }
                .onChange(of: valueString) {
                    value = Int(valueString)
                }
        }
    }
}
