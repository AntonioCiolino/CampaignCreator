import Foundation
import CampaignCreatorLib

class FeatureService {
    private let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    func fetchFeatures() async throws -> [Feature] {
        return try await apiService.performRequest(endpoint: "/features/")
    }
}
