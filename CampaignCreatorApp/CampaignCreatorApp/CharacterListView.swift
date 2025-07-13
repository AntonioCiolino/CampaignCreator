import SwiftUI
import Kingfisher

struct CharacterListView: View {
    @StateObject private var viewModel = CharacterListViewModel()
    @EnvironmentObject var imageUploadService: ImageUploadService
    @State private var showingCreateSheet = false

    var body: some View {
        NavigationView {
            Group {
                if viewModel.isLoading && viewModel.characters.isEmpty {
                    ProgressView("Loading Characters...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error = viewModel.errorMessage {
                    VStack {
                        Text("Error Loading Characters")
                            .font(.headline)
                        Text(error)
                            .font(.caption)
                            .multilineTextAlignment(.center)
                        Button("Retry") {
                            Task {
                                await viewModel.fetchCharacters()
                            }
                        }
                        .padding(.top)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if viewModel.characters.isEmpty {
                    Text("No characters yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(viewModel.characters) { character in
                            NavigationLink(destination: CharacterDetailView(character: character).environmentObject(imageUploadService)) {
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
                                        Text(character.description ?? "No description")
                                            .font(.subheadline)
                                            .foregroundColor(.gray)
                                            .lineLimit(2) // Limit description lines in list
                                    }
                                }
                            }
                        }
                        .onDelete(perform: deleteCharacters)
                    }
                    .refreshable {
                        print("CharacterListView: Refresh triggered. Fetching characters.")
                        await viewModel.fetchCharacters()
                    }
                }
            }
            .navigationTitle("Characters")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if viewModel.isLoading && !viewModel.characters.isEmpty {
                        ProgressView()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        self.showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet, onDismiss: {
                Task {
                    await viewModel.fetchCharacters()
                }
            }) {
                CharacterCreateView(isPresented: $showingCreateSheet)
            }
            .onAppear {
                Task {
                    await viewModel.fetchCharacters()
                }
            }
        }
    }

    private func deleteCharacters(offsets: IndexSet) {
        let charactersToDelete = offsets.map { viewModel.characters[$0] }
        Task {
            for character in charactersToDelete {
                await viewModel.deleteCharacter(character)
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
