import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterListViewModel: ObservableObject {
    @Published var characters: [Character] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = CampaignCreatorLib.APIService()

    func fetchCharacters() async {
        isLoading = true
        errorMessage = nil
        do {
            let fetchedCharacters: [Character] = try await apiService.fetchCharacters() as! [Character]
            self.characters = fetchedCharacters
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func deleteCharacter(_ character: Character) async {
        isLoading = true
        errorMessage = nil
        do {
            try await apiService.deleteCharacter(id: character.id)
            await fetchCharacters()
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
