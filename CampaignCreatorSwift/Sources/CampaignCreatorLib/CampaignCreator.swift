import Foundation

public class CampaignCreator {
    public let markdownGenerator: MarkdownGenerator
    private var llmService: LLMService?
    private var documents: [Document] = []
    
    public init() {
        self.markdownGenerator = MarkdownGenerator()
        self.setupLLMService()
    }
    
    private func setupLLMService() {
        // Try to initialize available LLM services
        do {
            self.llmService = try OpenAIClient()
            print("✅ OpenAI service initialized")
        } catch {
            print("⚠️  OpenAI service not available: \(error.localizedDescription)")
        }
        
        // Could add more services here (Gemini, etc.)
    }
    
    // MARK: - Document Management
    
    public func createDocument(title: String = "Untitled Document", text: String = "") -> Document {
        let document = Document(text: text, title: title)
        documents.append(document)
        return document
    }
    
    public func loadDocument(from url: URL) -> Document? {
        guard let document = Document(fromURL: url) else {
            return nil
        }
        documents.append(document)
        return document
    }
    
    public func saveDocument(_ document: Document, to url: URL) throws {
        try document.save(to: url)
        print("📝 Document saved to: \(url.path)")
    }
    
    public func listDocuments() -> [Document] {
        return documents
    }
    
    // MARK: - LLM Features
    
    public func generateText(prompt: String, completion: @escaping @Sendable (Result<String, LLMError>) -> Void) {
        guard let llmService = llmService else {
            completion(.failure(.other(message: "No LLM service available. Please set up API keys.")))
            return
        }
        
        print("🤖 Generating text with prompt: \(prompt.prefix(50))...")
        llmService.generateCompletion(prompt: prompt, completionHandler: completion)
    }
    
    @available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 6.0, *)
    public func generateText(prompt: String) async throws -> String {
        guard let llmService = llmService else {
            throw LLMError.other(message: "No LLM service available. Please set up API keys.")
        }
        
        print("🤖 Generating text with prompt: \(prompt.prefix(50))...")
        return try await llmService.generateCompletion(prompt: prompt)
    }
    
    // MARK: - Utility Functions
    
    public func showStatus() {
        print("\n=== Campaign Creator Status ===")
        print("Available Services: \(SecretsManager.shared.availableServices.joined(separator: ", "))")
        print("Documents loaded: \(documents.count)")
        if !documents.isEmpty {
            print("Documents:")
            for (index, doc) in documents.enumerated() {
                print("  \(index + 1). \(doc.title) (\(doc.wordCount) words)")
            }
        }
        print("================================\n")
    }
    
    public func exportToHomebrewery(_ document: Document) -> String {
        return markdownGenerator.generateHomebreweryMarkdown(from: document.text)
    }
}