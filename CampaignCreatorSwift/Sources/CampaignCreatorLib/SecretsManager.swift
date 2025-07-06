import Foundation

public struct SecretsManager: Sendable {
    
    public static let shared = SecretsManager()
    
    private init() {}
    
    public var openAIAPIKey: String? {
        return ProcessInfo.processInfo.environment["OPENAI_API_KEY"]
    }
    
    public var geminiAPIKey: String? {
        return ProcessInfo.processInfo.environment["GEMINI_API_KEY"]
    }
    
    public var antropicAPIKey: String? {
        return ProcessInfo.processInfo.environment["ANTHROPIC_API_KEY"]
    }
    
    /// Check if any API key is available
    public var hasAnyAPIKey: Bool {
        return openAIAPIKey != nil || geminiAPIKey != nil || antropicAPIKey != nil
    }
    
    /// Get available services
    public var availableServices: [String] {
        var services: [String] = []
        if openAIAPIKey != nil { services.append("OpenAI") }
        if geminiAPIKey != nil { services.append("Gemini") }
        if antropicAPIKey != nil { services.append("Anthropic") }
        return services
    }
    
    /// Validate that an API key is not a placeholder
    public func isValidKey(_ key: String?) -> Bool {
        guard let key = key else { return false }
        let placeholders = ["YOUR_API_KEY", "YOUR_OPENAI_API_KEY", "YOUR_GEMINI_API_KEY", "YOUR_ANTHROPIC_API_KEY"]
        return !key.isEmpty && !placeholders.contains(key)
    }
}