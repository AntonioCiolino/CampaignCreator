import Foundation
import CampaignCreatorLib

enum ImageGenerationError: Error, LocalizedError {
    case networkError(Error)
    case serverError(statusCode: Int, message: String?)
    case invalidResponse
    case decodingError(Error)
    case noToken

    var errorDescription: String? {
        switch self {
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .serverError(let statusCode, let message):
            return "Server error (\(statusCode)): \(message ?? "Unknown server error")"
        case .invalidResponse:
            return "Invalid response from server."
        case .decodingError(let error):
            return "Failed to decode server response: \(error.localizedDescription)"
        case .noToken:
            return "Authentication token not found."
        }
    }
}

@MainActor
class ImageGenerationService: ObservableObject {
    private let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    func generateImage(prompt: String, model: String = "dall-e-3") async throws -> String {
        guard let token = UserDefaultsTokenManager().getToken() else {
            throw ImageGenerationError.noToken
        }

        let endpoint = "/images/generate"
        let payload = ["prompt": prompt, "model": model]

        do {
            let response: FileUploadResponse = try await apiService.post(endpoint: endpoint, data: payload, token: token)
            return response.imageUrl
        } catch let error as APIServiceError {
            switch error {
            case .networkError(let underlyingError):
                throw ImageGenerationError.networkError(underlyingError)
            case .decodingError(let underlyingError):
                throw ImageGenerationError.decodingError(underlyingError)
            case .serverError(let statusCode, let message):
                throw ImageGenerationError.serverError(statusCode: statusCode, message: message)
            }
        }
    }
}
