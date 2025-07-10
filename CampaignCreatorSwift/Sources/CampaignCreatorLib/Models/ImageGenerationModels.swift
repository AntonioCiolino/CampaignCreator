import Foundation

public enum ImageModelName: String, Codable, Sendable, CaseIterable { // Added CaseIterable for potential pickers
    case openAIDalle = "dall-e" // Single case for DALL-E, rawValue matches backend
    case stableDiffusion = "stable-diffusion" // Example, actual value might differ
    case gemini // Assuming "gemini" is the raw value for Gemini models

    // Convenience for a default or common model
    public static var defaultOpenAI: ImageModelName { .openAIDalle }
}

public struct ImageGenerationParams: Codable, Sendable {
    public let prompt: String
    public let model: ImageModelName // e.g., "dall-e", "stable-diffusion"
    public let size: String?
    public let quality: String? // DALL-E specific
    public let steps: Int?      // Stable Diffusion specific
    public let cfgScale: Double? // Stable Diffusion specific (cfg_scale)
    public let geminiModelName: String? // Gemini specific
    public let campaignId: String? // String to match web, though Int might be better if always internal ID

    enum CodingKeys: String, CodingKey {
        case prompt, model, size, quality, steps
        case cfgScale = "cfg_scale"
        case geminiModelName = "gemini_model_name"
        case campaignId = "campaign_id"
    }

    public init(prompt: String, model: ImageModelName, size: String? = nil, quality: String? = nil, steps: Int? = nil, cfgScale: Double? = nil, geminiModelName: String? = nil, campaignId: String? = nil) {
        self.prompt = prompt
        self.model = model
        self.size = size
        self.quality = quality
        self.steps = steps
        self.cfgScale = cfgScale
        self.geminiModelName = geminiModelName
        self.campaignId = campaignId
    }
}

public struct ImageGenerationResponse: Codable, Sendable {
    public let imageUrl: String? // Changed to optional
    public let promptUsed: String?
    public let modelUsed: ImageModelName
    public let sizeUsed: String
    public let qualityUsed: String?
    public let stepsUsed: Int?
    public let cfgScaleUsed: Double?
    public let geminiModelNameUsed: String?

    enum CodingKeys: String, CodingKey {
        case imageUrl = "image_url"
        case promptUsed = "prompt_used"
        case modelUsed = "model_used"
        case sizeUsed = "size_used"
        case qualityUsed = "quality_used"
        case stepsUsed = "steps_used"
        case cfgScaleUsed = "cfg_scale_used"
        case geminiModelNameUsed = "gemini_model_name_used"
    }

    // Update init to accept optional imageUrl
    public init(imageUrl: String?, promptUsed: String?, modelUsed: ImageModelName, sizeUsed: String, qualityUsed: String? = nil, stepsUsed: Int? = nil, cfgScaleUsed: Double? = nil, geminiModelNameUsed: String? = nil) {
        self.imageUrl = imageUrl
        self.promptUsed = promptUsed
        self.modelUsed = modelUsed
        self.sizeUsed = sizeUsed
        self.qualityUsed = qualityUsed
        self.stepsUsed = stepsUsed
        self.cfgScaleUsed = cfgScaleUsed
        self.geminiModelNameUsed = geminiModelNameUsed
    }
}
