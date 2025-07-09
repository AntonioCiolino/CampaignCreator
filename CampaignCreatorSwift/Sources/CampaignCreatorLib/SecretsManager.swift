import Foundation

public struct SecretsManager: Sendable {
    
    public static let shared = SecretsManager()
    // private let userDefaults = UserDefaults.standard // Removed to ensure Sendable

    // Define constants for UserDefault keys to avoid typos
    private enum APIKeyNames: String {
        case openAI = "OPENAI_API_KEY"
        case gemini = "GEMINI_API_KEY"
        case anthropic = "ANTHROPIC_API_KEY"
        case stableDiffusion = "STABLE_DIFFUSION_API_KEY"
    }
    
    private init() {}
    
    public var openAIAPIKey: String? {
        let rawKey = UserDefaults.standard.string(forKey: APIKeyNames.openAI.rawValue)
        let valid = isValidKey(rawKey)
        print("[API_KEY_DEBUG SecretsManager] openAIAPIKey: Raw key from UserDefaults for '\(APIKeyNames.openAI.rawValue)': '\(rawKey ?? "nil")'. isValidKey: \(valid)")
        return valid ? rawKey : nil
    }
    
    public var geminiAPIKey: String? {
        let key = UserDefaults.standard.string(forKey: APIKeyNames.gemini.rawValue)
        return isValidKey(key) ? key : nil
    }
    
    public var antropicAPIKey: String? { // Corrected typo from antRopic to antHropic
        let key = UserDefaults.standard.string(forKey: APIKeyNames.anthropic.rawValue)
        return isValidKey(key) ? key : nil
    }

    public var stableDiffusionAPIKey: String? {
        let key = UserDefaults.standard.string(forKey: APIKeyNames.stableDiffusion.rawValue)
        return isValidKey(key) ? key : nil
    }
    
    /// Check if any API key is available
    public var hasAnyAPIKey: Bool {
        // Check each key; UserDefaults access is fine here as it's not stored.
        return (UserDefaults.standard.string(forKey: APIKeyNames.openAI.rawValue).flatMap(isValidKey) ?? false) ||
               (UserDefaults.standard.string(forKey: APIKeyNames.gemini.rawValue).flatMap(isValidKey) ?? false) ||
               (UserDefaults.standard.string(forKey: APIKeyNames.anthropic.rawValue).flatMap(isValidKey) ?? false) ||
               (UserDefaults.standard.string(forKey: APIKeyNames.stableDiffusion.rawValue).flatMap(isValidKey) ?? false)
    }
    
    /// Get available services
    public var availableServices: [String] {
        var services: [String] = []
        // Access UserDefaults directly for checks
        if UserDefaults.standard.string(forKey: APIKeyNames.openAI.rawValue).flatMap(isValidKey) ?? false { services.append("OpenAI") }
        if UserDefaults.standard.string(forKey: APIKeyNames.gemini.rawValue).flatMap(isValidKey) ?? false { services.append("Gemini") }
        if UserDefaults.standard.string(forKey: APIKeyNames.anthropic.rawValue).flatMap(isValidKey) ?? false { services.append("Anthropic") }
        if UserDefaults.standard.string(forKey: APIKeyNames.stableDiffusion.rawValue).flatMap(isValidKey) ?? false { services.append("Stable Diffusion") }
        return services
    }
    
    /// Validate that an API key is not a placeholder
    public func isValidKey(_ key: String?) -> Bool {
        guard let key = key else { return false }
        let placeholders = ["YOUR_API_KEY", "YOUR_OPENAI_API_KEY", "YOUR_GEMINI_API_KEY", "YOUR_ANTHROPIC_API_KEY"]
        return !key.isEmpty && !placeholders.contains(key)
    }
}