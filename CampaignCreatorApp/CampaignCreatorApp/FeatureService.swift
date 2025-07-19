import Foundation
import CampaignCreatorLib

class FeatureService {
    private let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    @Environment(\.modelContext) private var modelContext

    func fetchFeatures() async throws -> [Feature] {
        let descriptor = FetchDescriptor<FeatureModel>()
        let localFeatures = try? modelContext.fetch(descriptor)

        if let localFeatures = localFeatures, !localFeatures.isEmpty {
            return localFeatures.map { Feature(id: $0.id, name: $0.name, template: $0.template, user_id: $0.user_id, required_context: $0.required_context, compatible_types: $0.compatible_types, feature_category: $0.feature_category) }
        } else {
            do {
                let features: [Feature] = try await apiService.performRequest(endpoint: "/features/")
                for feature in features {
                    let featureModel = FeatureModel(id: feature.id, name: feature.name, template: feature.template, user_id: feature.user_id, required_context: feature.required_context, compatible_types: feature.compatible_types, feature_category: feature.feature_category)
                    modelContext.insert(featureModel)
                }
                try modelContext.save()
                return features
            } catch {
                throw error
            }
        }
    }
}
