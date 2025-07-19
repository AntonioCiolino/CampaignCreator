import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterImageManagerViewModel: ImageManagerViewModel {
    let characterID: Int

    init(imageURLs: Binding<[String]>, characterID: Int) {
        self.characterID = characterID
        super.init(imageURLs: imageURLs)
    }
}

struct CharacterImageGenerationResponse: Codable {
    let image_url: String?
    let prompt_used: String
}
