import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterDetailViewModel: ObservableObject {
    @Published var character: Character
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = CampaignCreatorLib.APIService()

    init(character: Character) {
        self.character = character
    }

    func refreshCharacter() async {
        isLoading = true
        errorMessage = nil
        do {
            let refreshedCharacter: Character = try await apiService.fetchCharacter(id: character.id) as! Character
            self.character = refreshedCharacter
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
