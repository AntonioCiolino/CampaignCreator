import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterMoodboardViewModel: ObservableObject {
    @Published var character: Character
    @Published var imageURLs: [String]

    private var apiService = CampaignCreatorLib.APIService()

    init(character: Character) {
        self.character = character
        self.imageURLs = character.image_urls ?? []
    }

}
