import Foundation
import SwiftUI

@MainActor
class CharacterListViewModel: ObservableObject {
    @Published var characters: [Character] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = APIService()

    func fetchCharacters() async {
        isLoading = true
        errorMessage = nil
        do {
            let fetchedCharacters: [Character] = try await apiService.performRequest(endpoint: "/characters/")
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
            try await apiService.performVoidRequest(endpoint: "/characters/\\(character.id)", method: "DELETE")
            await fetchCharacters()
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
