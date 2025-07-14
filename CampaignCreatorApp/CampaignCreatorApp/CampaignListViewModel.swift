import Foundation
import SwiftUI
import SwiftData

@MainActor
class CampaignListViewModel: ObservableObject {
    @Published var campaigns: [Campaign] = []
    private var modelContext: ModelContext?

    func setModelContext(_ context: ModelContext) {
        self.modelContext = context
        fetchCampaigns()
    }

    func fetchCampaigns() {
        guard let context = modelContext else { return }
        do {
            let descriptor = FetchDescriptor<Campaign>(sortBy: [SortDescriptor(\.title)])
            self.campaigns = try context.fetch(descriptor)
        } catch {
            // Handle error
        }
    }

    func deleteCampaign(_ campaign: Campaign) {
        guard let context = modelContext else { return }
        context.delete(campaign)
        do {
            try context.save()
            fetchCampaigns()
        } catch {
            // Handle error
        }
    }
}
