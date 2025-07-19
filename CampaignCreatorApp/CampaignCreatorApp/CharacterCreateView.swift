import SwiftUI 
import SwiftData

struct CharacterCreateView: View {
    @Environment(\.modelContext) private var modelContext
    @Binding var isPresented: Bool
    var ownerId: Int
    
    @State private var name = ""
    @State private var character_description = ""
    @State private var appearance_description = ""
    @State private var image_urls: [String] = []
    @State private var newImageURL = ""
    @State private var notes_for_llm = ""
    @State private var export_format_preference = "Complex"
    @State private var strength: Int? = 10
    @State private var dexterity: Int? = 10
    @State private var constitution: Int? = 10
    @State private var intelligence: Int? = 10
    @State private var wisdom: Int? = 10
    @State private var charisma: Int? = 10
    
    init(isPresented: Binding<Bool>, ownerId: Int) {
        _isPresented = isPresented
        self.ownerId = ownerId
        print("CharacterCreateView init")
    }
    
    var body: some View {
        print("CharacterCreateView body")
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
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
                
                Section(header: Text("Statistics")) {
                    StatEditableRow(label: "Strength", value: $strength)
                    StatEditableRow(label: "Dexterity", value: $dexterity)
                    StatEditableRow(label: "Constitution", value: $constitution)
                    StatEditableRow(label: "Intelligence", value: $intelligence)
                    StatEditableRow(label: "Wisdom", value: $wisdom)
                    StatEditableRow(label: "Charisma", value: $charisma)
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
            print("Attempting to save character with name: \(name) and owner_id: \(ownerId)")
            let newCharacter = CharacterModel(
                id: 0,
                name: name,
                character_description: character_description,
                appearance_description: appearance_description,
                image_urls: image_urls,
                notes_for_llm: notes_for_llm,
                strength: strength,
                dexterity: dexterity,
                constitution: constitution,
                intelligence: intelligence,
                wisdom: wisdom,
                charisma: charisma,
                export_format_preference: export_format_preference,
                owner_id: ownerId
            )
            modelContext.insert(newCharacter)
            
            do {
                try modelContext.save()
                print("Successfully saved model context from saveCharacter.")
            } catch {
                print("Error saving model context from saveCharacter: \(error.localizedDescription)")
            }
        }
    }

