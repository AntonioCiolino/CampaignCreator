import SwiftUI
import Kingfisher
import SwiftData

struct CharacterListView: View {
    @Environment(\.modelContext) private var modelContext
    @EnvironmentObject var contentViewModel: ContentViewModel
    @Query(sort: \CharacterModel.name) private var characters: [CharacterModel]
    @State private var showingCreateSheet = false
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""

    private let apiService = CampaignCreatorLib.APIService()

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
                    .refreshable {
                        await refreshCharacters()
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
            .alert("Error", isPresented: $showingErrorAlert) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }

    private func deleteCharacters(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                let characterToDelete = characters[index]
                print("Attempting to delete character: \(characterToDelete.name)")
                modelContext.delete(characterToDelete)
            }

            do {
                try modelContext.save()
                print("Successfully saved model context from deleteCharacters.")
            } catch {
                print("Error saving model context from deleteCharacters: \(error.localizedDescription)")
            }
        }
    }

    private func refreshCharacters() async {
        guard let token = UserDefaultsTokenManager().getToken() else {
            errorMessage = "Authentication token not found."
            showingErrorAlert = true
            return
        }

        do {
            let fetchedCharacters: [CharacterModel] = try await apiService.get(endpoint: "/characters", token: token)

            // Clear out existing characters to avoid duplicates
            for character in characters {
                modelContext.delete(character)
            }

            // Insert new characters
            for character in fetchedCharacters {
                modelContext.insert(character)
            }

            try modelContext.save()
        } catch {
            errorMessage = "Failed to refresh characters: \(error.localizedDescription)"
            showingErrorAlert = true
        }
    }
}

