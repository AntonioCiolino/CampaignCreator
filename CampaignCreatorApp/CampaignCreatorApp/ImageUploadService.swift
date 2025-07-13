import Foundation
import CampaignCreatorLib

enum ImageUploadError: Error, LocalizedError {
    case networkError(Error)
    case serverError(statusCode: Int, message: String?)
    case invalidResponse
    case decodingError(Error)
    case noToken
    case invalidURL

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
        case .invalidURL:
            return "The upload URL was invalid."
        }
    }
}

struct FileUploadResponse: Decodable {
    let imageUrl: String
}

class ImageUploadService: ObservableObject {
    private let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    func uploadImage(imageData: Data, filename: String, mimeType: String) async -> Result<String, ImageUploadError> {
        guard let token = CampaignCreatorLib.UserDefaultsTokenManager().getToken() else {
            return .failure(.noToken)
        }

        let endpointPath = "/files/upload_image"
        guard let url = URL(string: apiService.baseURLString.stripSuffix("/") + endpointPath) else {
            return .failure(.invalidURL)
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                return .failure(.invalidResponse)
            }

            if (200..<300).contains(httpResponse.statusCode) {
                do {
                    let decodedResponse = try JSONDecoder().decode(FileUploadResponse.self, from: data)
                    return .success(decodedResponse.imageUrl)
                } catch {
                    return .failure(.decodingError(error))
                }
            } else {
                let errorBody = String(data: data, encoding: .utf8)
                return .failure(.serverError(statusCode: httpResponse.statusCode, message: errorBody))
            }
        } catch {
            return .failure(.networkError(error))
        }
    }
}

// Helper extension for String to strip suffix if present - ensuring it's available
// This might already be in CampaignDetailView, but good to have it here if this service
// is ever moved or used more independently. If it causes a redeclaration error,
// it means it's correctly defined elsewhere and accessible.
// The StringUtils.swift file now provides this extension for the app target.
