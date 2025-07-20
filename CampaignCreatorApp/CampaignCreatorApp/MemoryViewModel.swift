import Foundation
import SwiftUI
import SwiftData
import CampaignCreatorLib

@MainActor
class MemoryViewModel: ObservableObject {
    @Published var memory: MemoryModel
    @Published var errorMessage: String?

    private var modelContext: ModelContext
    private var apiService = CampaignCreatorLib.APIService()

    init(memory: MemoryModel, modelContext: ModelContext) {
        self.memory = memory
        self.modelContext = modelContext
    }

    func forceSummarizeMemory(completion: @escaping () -> Void) {
        guard let characterId = memory.character?.id else {
            completion()
            return
        }
        Task {
            do {
                let summary: MemorySummary = try await apiService.performRequest(endpoint: "/characters/\(characterId)/force-memory-summary", method: "POST")
                memory.summary = summary.memory_summary ?? ""
                memory.timestamp = Date()
                try? modelContext.save()
            } catch {
                errorMessage = "Failed to force memory summarization: \(error.localizedDescription)"
            }
            completion()
        }
    }

}
