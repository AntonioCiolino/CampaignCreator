import Foundation

public struct SecretsManager: Sendable {
    
    public static let shared = SecretsManager()
    private let userDefaults = UserDefaults.standard

    // Define constants for UserDefault keys to avoid typos
    private enum APIKeyNames: String {
        case openAI = "OPENAI_API_KEY"
        case gemini = "GEMINI_API_KEY"
        case anthropic = "ANTHROPIC_API_KEY"
        // Add Stable Diffusion key name when implemented
        case stableDiffusion = "STABLE_DIFFUSION_API_KEY"
    }
    
    private init() {}
    
    public var openAIAPIKey: String? {
        let key = userDefaults.string(forKey: APIKeyNames.openAI.rawValue)
        return isValidKey(key) ? key : nil
    }
    
    public var geminiAPIKey: String? {
        let key = userDefaults.string(forKey: APIKeyNames.gemini.rawValue)
        return isValidKey(key) ? key : nil
    }
    
    public var antropicAPIKey: String? { // Corrected typo from antRopic to antHropic
        let key = userDefaults.string(forKey: APIKeyNames.anthropic.rawValue)
        return isValidKey(key) ? key : nil
    }

    public var stableDiffusionAPIKey: String? { // Added for Stable Diffusion
        let key = userDefaults.string(forKey: APIKeyNames.stableDiffusion.rawValue)
        return isValidKey(key) ? key : nil
    }
    
    /// Check if any API key is available
    public var hasAnyAPIKey: Bool {
        return openAIAPIKey != nil || geminiAPIKey != nil || antropicAPIKey != nil || stableDiffusionAPIKey != nil
    }
    
    /// Get available services
    public var availableServices: [String] {
        var services: [String] = []
        if openAIAPIKey != nil { services.append("OpenAI") }
        if geminiAPIKey != nil { services.append("Gemini") }
        if antropicAPIKey != nil { services.append("Anthropic") } // Corrected typo
        if stableDiffusionAPIKey != nil { services.append("Stable Diffusion") }
        return services
    }
    
    /// Validate that an API key is not a placeholder
    public func isValidKey(_ key: String?) -> Bool {
        guard let key = key else { return false }
        let placeholders = ["YOUR_API_KEY", "YOUR_OPENAI_API_KEY", "YOUR_GEMINI_API_KEY", "YOUR_ANTHROPIC_API_KEY"]
        return !key.isEmpty && !placeholders.contains(key)
    }
}