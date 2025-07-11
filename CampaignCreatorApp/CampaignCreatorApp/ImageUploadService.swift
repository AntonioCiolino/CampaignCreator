import Foundation
import CampaignCreatorLib // For APIService and potentially error types

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
    // Add other fields if needed, like filename, content_type, size,
    // matching the backend's FileUploadResponse Pydantic model.
    // For now, only imageUrl is strictly needed by the caller.
}

class ImageUploadService: ObservableObject { // Conform to ObservableObject
    private let apiService: APIService

    init(apiService: APIService) {
        self.apiService = apiService
    }

    func uploadImage(imageData: Data, filename: String, mimeType: String) async -> Result<String, ImageUploadError> {
        guard let token = apiService.getToken() else {
            return .failure(.noToken)
        }

        let endpointPath = "/files/upload_image" // From file_uploads.py in backend
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

            print("[ImageUploadService] Upload response status code: \(httpResponse.statusCode)")

            if (200..<300).contains(httpResponse.statusCode) {
                do {
                    let decodedResponse = try JSONDecoder().decode(FileUploadResponse.self, from: data)
                    print("[ImageUploadService] Image uploaded successfully. URL: \(decodedResponse.imageUrl)")
                    return .success(decodedResponse.imageUrl)
                } catch {
                    print("[ImageUploadService] Failed to decode upload response: \(error), data: \(String(data: data, encoding: .utf8) ?? "empty")")
                    return .failure(.decodingError(error))
                }
            } else {
                let errorBody = String(data: data, encoding: .utf8)
                print("[ImageUploadService] Upload error response (\(httpResponse.statusCode)): \(errorBody ?? "No error body")")
                return .failure(.serverError(statusCode: httpResponse.statusCode, message: errorBody))
            }
        } catch {
            print("[ImageUploadService] Image upload request failed: \(error.localizedDescription)")
            return .failure(.networkError(error))
        }
    }
}

// Helper extension for String to strip suffix if present - ensuring it's available
// This might already be in CampaignDetailView, but good to have it here if this service
// is ever moved or used more independently. If it causes a redeclaration error,
// it means it's correctly defined elsewhere and accessible.
// To avoid potential conflicts, assuming it's accessible from another file.
// If not, uncomment this:
/*
extension String {
    func stripSuffix(_ suffix: String) -> String {
        if self.hasSuffix(suffix) {
            return String(self.dropLast(suffix.count))
        }
        return self
    }
}
*/
