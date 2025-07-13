import Foundation

class FeatureService {
    private let apiService: APIService

    init(apiService: APIService = APIService()) {
        self.apiService = apiService
    }

    func fetchFeatures() async throws -> [Feature] {
        return try await apiService.performRequest(endpoint: "/features/")
    }
}
