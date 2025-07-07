import SwiftUI
import CampaignCreatorLib

struct CharacterListView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @State private var showingCreateSheet = false

    var body: some View {
        NavigationView {
            Group {
                if campaignCreator.isLoadingCharacters && campaignCreator.characters.isEmpty {
                    ProgressView("Loading Characters...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error = campaignCreator.characterError {
                    VStack {
                        Text("Error Loading Characters")
                            .font(.headline)
                        Text(error.localizedDescription)
                            .font(.caption)
                            .multilineTextAlignment(.center)
                        Button("Retry") {
                            Task {
                                await campaignCreator.fetchCharacters()
                            }
                        }
                        .padding(.top)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if campaignCreator.characters.isEmpty {
                    Text("No characters yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(campaignCreator.characters) { character in
                            NavigationLink(destination: CharacterDetailView(character: character, campaignCreator: campaignCreator)) {
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
                        .onDelete(perform: deleteCharacters)
                    }
                }
            }
            .navigationTitle("Characters")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if campaignCreator.isLoadingCharacters && !campaignCreator.characters.isEmpty {
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
                // CharacterCreateView calls fetchCharacters internally upon successful save via CampaignCreator
            }) {
                CharacterCreateView(campaignCreator: campaignCreator, isPresented: $showingCreateSheet)
            }
            .onAppear {
                // Simplified logic:
                // Proactive fetch is now handled in CampaignCreator after successful user session validation.
                // This .onAppear primarily handles:
                // 1. Retrying if there was a previous error.
                // 2. Fetching if the view appears and characters are empty AND the initial fetch (now proactive)
                //    hasn't been marked as attempted yet (e.g., view appears *very* quickly).
                print("CharacterListView: .onAppear. SessionValid: \(campaignCreator.isUserSessionValid), Auth: \(campaignCreator.isAuthenticated), Loading: \(campaignCreator.isLoadingCharacters), CharactersEmpty: \(campaignCreator.characters.isEmpty), InitialFetchAttempted: \(campaignCreator.initialCharacterFetchAttempted), Err: \(campaignCreator.characterError != nil ? (campaignCreator.characterError?.localizedDescription ?? "Unknown Error") : "None")")
                if campaignCreator.isUserSessionValid && !campaignCreator.isLoadingCharacters {
                    // Fetch if there's an error to retry, OR
                    // if characters are empty and initial fetch hasn't been attempted (less likely now but safe).
                    if campaignCreator.characterError != nil || (campaignCreator.characters.isEmpty && !campaignCreator.initialCharacterFetchAttempted) {
                        print("CharacterListView: Conditions met for fetch (error retry or initial empty state). Will fetch characters.")
                        Task {
                            await campaignCreator.fetchCharacters()
                        }
                    } else {
                        print("CharacterListView: Skipping fetch. Conditions not met (no error, or characters present/initial fetch attempted). Characters count: \(campaignCreator.characters.count)")
                    }
                } else {
                    print("CharacterListView: Skipping fetch. Session not valid or already loading. SessionValid: \(campaignCreator.isUserSessionValid), Loading: \(campaignCreator.isLoadingCharacters)")
                }
            }
        }
    }

    private func deleteCharacters(offsets: IndexSet) {
        let charactersToDelete = offsets.map { campaignCreator.characters[$0] }
        Task {
            for character in charactersToDelete {
                do {
                    try await campaignCreator.deleteCharacter(character)
                } catch {
                    print("Error deleting character \(character.name): \(error.localizedDescription)")
                    // TODO: Show alert to user about deletion failure
                }
            }
            // CampaignCreator's deleteCharacter method already calls fetchCharacters,
            // which will update the @Published characters array.
        }
    }
}

#Preview {
    let previewCreator = CampaignCreator()
    // For preview, populate with some mock data directly if API is not live
    // This requires CampaignCreator's characters array to be settable or to have a mock data init.
    // For simplicity, this preview will show loading or empty state if API not running.
    // To show data, you could do:
    /*
    previewCreator.characters = [
        Character(id: 1, name: "Preview Elara", description: "Preview Elf Ranger. A long description to test line limits and see how it wraps or truncates based on the view settings for this particular character entry in the list view."), // Added id: 1
        Character(id: 2, name: "Preview Grom", description: "Preview Orc Warrior") // Added id: 2
    ]
    */
    return CharacterListView(campaignCreator: previewCreator)
}
