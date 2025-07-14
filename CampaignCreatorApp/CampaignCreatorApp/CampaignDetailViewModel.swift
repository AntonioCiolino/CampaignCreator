import Foundation
import SwiftUI
import SwiftData

@MainActor
class CampaignDetailViewModel: ObservableObject {
    @Published var campaign: Campaign
    private var modelContext: ModelContext?

    init(campaign: Campaign) {
        self.campaign = campaign
    }

    func setModelContext(_ context: ModelContext) {
        self.modelContext = context
    }

    // Use this context in your async logic, e.g.
    func refreshCampaign() async {
        guard let context = modelContext else { return }
        // Fetch or update with context.fetch(...) etc.
    }
}
