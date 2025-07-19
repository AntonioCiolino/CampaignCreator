import Foundation

enum ImageModelName: String, CaseIterable, Codable {
    case dalle3 = "dall-e-3"
    case dalle2 = "dall-e-2"
    case openAIDalle = "dall-e"
    case stableDiffusion = "stable-diffusion"
}
