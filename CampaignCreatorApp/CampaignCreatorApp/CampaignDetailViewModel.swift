import Foundation
import SwiftUI
import SwiftData

@MainActor
class CampaignDetailViewModel: ObservableObject {
    @Published var campaign: Campaign
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var modelContext: ModelContext

    init(campaign: Campaign, modelContext: ModelContext) {
        self.campaign = campaign
        self.modelContext = modelContext
    }
}
