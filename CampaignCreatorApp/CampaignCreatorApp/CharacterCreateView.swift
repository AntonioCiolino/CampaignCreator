import SwiftUI
import SwiftData

struct CharacterCreateView: View {
    @Environment(\.modelContext) private var modelContext
    @Binding var isPresented: Bool

    @State private var name = ""
    @State private var character_description = ""
    @State private var appearance_description = ""
    @State private var image_urls: [String] = []
    @State private var newImageURL = ""
    @State private var notes_for_llm = ""
    @State private var export_format_preference = "Complex"

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Character Details")) {
                    TextField("Name*", text: $name)
                    VStack(alignment: .leading) {
                        Text("Description").font(.caption)
                        TextEditor(text: $character_description).frame(height: 100)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                    VStack(alignment: .leading) {
                        Text("Appearance").font(.caption)
                        TextEditor(text: $appearance_description).frame(height: 100)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                }

                Section(header: Text("Image URLs")) {
                    ForEach(image_urls.indices, id: \.self) { index in
                        HStack {
                            TextField("Image URL", text: $image_urls[index])
                            Button(action: { image_urls.remove(at: index) }) {
                                Image(systemName: "trash").foregroundColor(.red)
                            }
                        }
                    }
                    HStack {
                        TextField("Add new image URL", text: $newImageURL)
                        Button(action: {
                            if !newImageURL.isEmpty, let _ = URL(string: newImageURL) {
                                image_urls.append(newImageURL)
                                newImageURL = ""
                            }
                        }) {
                            Image(systemName: "plus.circle.fill")
                        }
                        .disabled(newImageURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }

                Section(header: Text("Additional Information")) {
                    VStack(alignment: .leading) {
                        Text("Notes for LLM (Optional)").font(.caption).foregroundColor(.gray)
                        TextEditor(text: $notes_for_llm)
                            .frame(height: 80)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                    TextField("Export Format Preference", text: $export_format_preference)
                }
            }
            .navigationTitle("New Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        isPresented = false
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        saveCharacter()
                        isPresented = false
                    }
                    .disabled(name.isEmpty)
                }
            }
        }
    }

    private func saveCharacter() {
        let newCharacter = Character(
            name: name,
            character_description: character_description,
            appearance_description: appearance_description,
            image_urls: image_urls,
            notes_for_llm: notes_for_llm,
            export_format_preference: export_format_preference,
            owner_id: 0
        )
        modelContext.insert(newCharacter)
    }
}
