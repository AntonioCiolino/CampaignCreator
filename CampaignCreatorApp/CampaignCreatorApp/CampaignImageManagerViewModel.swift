import SwiftUI

@MainActor
class CampaignImageManagerViewModel: ImageManagerViewModel {
    let campaignID: Int

    init(imageURLs: Binding<[String]>, campaignID: Int) {
        self.campaignID = campaignID
        super.init(imageURLs: imageURLs)
    }
}
