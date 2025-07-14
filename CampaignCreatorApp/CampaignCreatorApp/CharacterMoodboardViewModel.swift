import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterMoodboardViewModel: ObservableObject {
    @Published var character: CharacterModel
    @Published var imageURLs: [String]

    private var apiService = CampaignCreatorLib.APIService()

    init(character: CharacterModel) {
        self.character = character
        self.imageURLs = character.image_urls ?? []
    }

}
