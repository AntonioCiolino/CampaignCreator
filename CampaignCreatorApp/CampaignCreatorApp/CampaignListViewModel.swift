import Foundation
import SwiftUI
import SwiftData

@MainActor
class CampaignListViewModel: ObservableObject {
    private var modelContext: ModelContext?

    func setModelContext(_ context: ModelContext) {
        self.modelContext = context
    }
}
