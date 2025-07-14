import SwiftUI
import Kingfisher
import SwiftData

struct CharacterListView: View {
    @EnvironmentObject var contentViewModel: ContentViewModel
    @State private var characters: [CampaignCreatorLib.Character] = []
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
                                    if let firstImageURL = character.imageURLs?.first, let url = URL(string: firstImageURL) {
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
                if let user = contentViewModel.currentUser {
                    CharacterCreateView(isPresented: $showingCreateSheet, ownerId: user.id)
                }
            }
        }
        .onAppear {
            fetchCharacters()
        }
    }

    private func fetchCharacters() {
        Task {
            do {
                characters = try await CampaignCreator.shared.fetchCharacters()
            } catch {
                print("Error fetching characters: \(error.localizedDescription)")
            }
        }
    }

    private func deleteCharacters(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                let characterToDelete = characters[index]
                print("Attempting to delete character: \(characterToDelete.name)")
                Task {
                    do {
                        try await CampaignCreator.shared.deleteCharacter(characterToDelete)
                        fetchCharacters()
                    } catch {
                        print("Error deleting character: \(error.localizedDescription)")
                    }
                }
            }
        }
    }
}

