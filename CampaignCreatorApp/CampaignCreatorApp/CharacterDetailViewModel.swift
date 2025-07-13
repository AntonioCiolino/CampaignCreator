import Foundation
import SwiftUI

@MainActor
class CharacterDetailViewModel: ObservableObject {
    @Published var character: Character
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = APIService()

    init(character: Character) {
        self.character = character
    }

    func refreshCharacter() async {
        isLoading = true
        errorMessage = nil
        do {
            let refreshedCharacter: Character = try await apiService.performRequest(endpoint: "/characters/\\(character.id)")
            self.character = refreshedCharacter
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
