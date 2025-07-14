import SwiftUI
import Kingfisher
import SwiftData

struct CharacterListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Character.name) private var characters: [Character]
    @State private var showingCreateSheet = false

    var body: some View {
        NavigationView {
            Group {
                if characters.isEmpty {
                    Text("No characters yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(characters) { character in
                            NavigationLink(destination: CharacterDetailView(character: character)) {
                                HStack {
                                    if let firstImageURL = character.image_urls?.first, let url = URL(string: firstImageURL) {
                                        KFImage(url)
                                            .resizable()
                                            .aspectRatio(contentMode: .fill)
                                            .frame(width: 40, height: 40)
                                            .clipped()
                                            .cornerRadius(4)
                                    } else {
                                        Image(systemName: "person.fill")
                                            .resizable()
                                            .aspectRatio(contentMode: .fit)
                                            .frame(width: 40, height: 40)
                                            .foregroundColor(.gray)
                                    }
                                    VStack(alignment: .leading) {
                                        Text(character.name)
                                            .font(.headline)
                                        Text(character.character_description ?? "No description")
                                            .font(.subheadline)
                                            .foregroundColor(.gray)
                                            .lineLimit(2) // Limit description lines in list
                                    }
                                }
                            }
                        }
                        .onDelete(perform: deleteCharacters)
                    }
                }
            }
            .navigationTitle("Characters")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        self.showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet) {
                CharacterCreateView(isPresented: $showingCreateSheet)
            }
        }
    }

    private func deleteCharacters(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                modelContext.delete(characters[index])
            }
        }
    }
}

#if DEBUG
struct CharacterListView_Previews: PreviewProvider {
    static var previews: some View {
        let viewModel = CharacterListViewModel()
        viewModel.characters = [
            Character(id: 1, owner_id: 1, name: "Preview Elara", description: "Preview Elf Ranger. A long description to test line limits and see how it wraps or truncates based on the view settings for this particular character entry in the list view.", image_urls: [], video_clip_urls: [], notes_for_llm: nil, stats: nil, export_format_preference: nil),
            Character(id: 2, owner_id: 1, name: "Preview Grom", description: "Preview Orc Warrior", image_urls: [], video_clip_urls: [], notes_for_llm: nil, stats: nil, export_format_preference: nil)
        ]

        return CharacterListView()
            .environmentObject(ImageUploadService(apiService: CampaignCreatorLib.APIService()))
    }
}
#endif
