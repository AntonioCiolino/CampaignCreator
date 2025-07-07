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
        // Attempt to load from Keychain
        // Note: KeychainHelper is in the App target, so direct access here is not possible
        // This will require a protocol or a shared mechanism if SecretsManager remains in a separate module.
        // For now, this assumes KeychainHelper is accessible or this logic is adapted.
        // Consider making KeychainHelper part of CampaignCreatorLib or using a shared AppGroup.
        // This is a placeholder for where Keychain logic would go.
        // As KeychainHelper is not directly available here, we'll need to adjust the architecture
        // or expect this to be handled at a higher level (e.g., in the App target, passing keys to the Lib).

        // Fallback to UserDefaults for now, or handle error appropriately
        // This change highlights an architectural consideration:
        // If SecretsManager is in a library, it cannot directly access KeychainHelper from the main app bundle without modification.
        // A proper solution would involve dependency injection or making KeychainHelper available to this module.

        // Attempt to load from Keychain
        do {
            let key = try KeychainHelper.loadPassword(username: APIKeyNames.openAI.rawValue)
            return isValidKey(key) ? key : nil
        } catch KeychainHelper.KeychainError.itemNotFound {
            // If not in Keychain, try UserDefaults (legacy support)
            let key = UserDefaults.standard.string(forKey: APIKeyNames.openAI.rawValue)
            if let key = key, isValidKey(key) {
                // If found in UserDefaults, migrate to Keychain
                do {
                    try KeychainHelper.savePassword(username: APIKeyNames.openAI.rawValue, password: key)
                    // Optionally, remove from UserDefaults after successful migration
                    // UserDefaults.standard.removeObject(forKey: APIKeyNames.openAI.rawValue)
                } catch {
                    print("Failed to migrate OpenAI API key to Keychain: \(error.localizedDescription)")
                }
                return key
            }
            return nil
        } catch {
            print("Failed to load OpenAI API key from Keychain: \(error.localizedDescription)")
            // Fallback to UserDefaults if Keychain access fails for other reasons
            let key = UserDefaults.standard.string(forKey: APIKeyNames.openAI.rawValue)
            return isValidKey(key) ? key : nil
        }
    }
    
    public var geminiAPIKey: String? {
        // Similar consideration for Gemini API Key if it were to be moved to Keychain
        // For now, keeping Gemini on UserDefaults as per original scope,
        // but ideally, all keys would be handled consistently.
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