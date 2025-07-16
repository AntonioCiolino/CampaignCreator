import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterDetailViewModel: ObservableObject {
    private var apiService = CampaignCreatorLib.APIService()

    func refreshCharacter(character: CharacterModel) async {
        // In a real app, you would fetch the latest character data from the server.
        // For now, we'll just print a message.
        print("Refreshing character...")
    }
}
