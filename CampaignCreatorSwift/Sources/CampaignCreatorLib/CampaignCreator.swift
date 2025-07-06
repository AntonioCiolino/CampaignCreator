import Foundation
#if canImport(Combine)
import Combine
#endif

public class CampaignCreator: ObservableObjectProtocol {
    public let markdownGenerator: MarkdownGenerator
    private var llmService: LLMService?

    #if canImport(Combine)
    @Published private var campaigns: [Campaign] = []
    @Published private var characters: [Character] = []
    #else
    private var campaigns: [Campaign] = []
    private var characters: [Character] = []
    #endif
    
    public init() {
        self.markdownGenerator = MarkdownGenerator()
        self.setupLLMService()
        // TODO: Load campaigns and characters from persistent storage
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
    
    // MARK: - Campaign Management
    
    public func createCampaign(title: String = "Untitled Campaign") -> Campaign {
        let campaign = Campaign(title: title)
        campaigns.append(campaign)
        // TODO: Save campaigns to persistent storage
        return campaign
    }
    
    public func loadCampaign(from url: URL) -> Campaign? {
        do {
            let campaign = try Campaign.load(from: url)
            // Avoid duplicates if already loaded
            if !campaigns.contains(where: { $0.id == campaign.id }) {
                campaigns.append(campaign)
            }
            return campaign
        } catch {
            print("Error loading campaign from \(url.path): \(error)")
            return nil
        }
    }
    
    public func saveCampaign(_ campaign: Campaign, to url: URL? = nil) throws {
        let saveURL = url ?? campaign.fileURL ?? defaultURLForCampaign(campaign)
        try campaign.save(to: saveURL)
        // Update fileURL in campaign if it was nil
        if var mutableCampaign = campaigns.first(where: { $0.id == campaign.id }), mutableCampaign.fileURL == nil {
            mutableCampaign.fileURL = saveURL
            updateCampaign(mutableCampaign)
        }
        print("📝 Campaign saved to: \(saveURL.path)")
        // TODO: Update campaigns list in persistent storage
    }

    private func defaultURLForCampaign(_ campaign: Campaign) -> URL {
        // Create a default URL in documents directory
        let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return documentsDirectory.appendingPathComponent("\(campaign.title.replacingOccurrences(of: " ", with: "_"))-\(campaign.id).json")
    }

    public func listCampaigns() -> [Campaign] {
        return campaigns
    }

    public func updateCampaign(_ campaign: Campaign) {
        if let index = campaigns.firstIndex(where: { $0.id == campaign.id }) {
            campaigns[index] = campaign
            // TODO: Save updated campaign to persistent storage
        }
    }

    public func deleteCampaign(_ campaign: Campaign) {
        campaigns.removeAll { $0.id == campaign.id }
        // TODO: Delete from persistent storage
        if let fileURL = campaign.fileURL {
            try? FileManager.default.removeItem(at: fileURL)
        }
    }
    
    // MARK: - Character Management

    public func createCharacter(name: String) -> Character {
        let character = Character(name: name)
        characters.append(character)
        // TODO: Save characters to persistent storage
        return character
    }

    public func listCharacters() -> [Character] {
        return characters
    }

    public func updateCharacter(_ character: Character) {
        if let index = characters.firstIndex(where: { $0.id == character.id }) {
            characters[index] = character
            // TODO: Save updated character to persistent storage
        }
    }
    
    public func deleteCharacter(_ character: Character) {
        characters.removeAll { $0.id == character.id }
        // TODO: Delete from persistent storage
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
        print("\n=== Campaign Crafter Status ===")
        print("Available Services: \(SecretsManager.shared.availableServices.joined(separator: ", "))")
        print("Campaigns loaded: \(campaigns.count)")
        if !campaigns.isEmpty {
            print("Campaigns:")
            for (index, campaign) in campaigns.enumerated() {
                print("  \(index + 1). \(campaign.title) (\(campaign.wordCount) words), \(campaign.sections.count) sections")
            }
        }
        print("Characters loaded: \(characters.count)")
        if !characters.isEmpty {
            print("Characters:")
            for (index, character) in characters.enumerated() {
                print("  \(index + 1). \(character.name)")
            }
        }
        print("================================\n")
    }
    
    public func exportCampaignToHomebrewery(_ campaign: Campaign) -> String {
        // This will likely need to be more sophisticated, combining all sections,
        // potentially using TOC, etc. For now, let's assume a simple concatenation
        // or export of the first section if it exists.
        // A more robust implementation would iterate through campaign.sections
        // and format them appropriately.
        let combinedText = campaign.sections.map { section in
            var text = ""
            if let title = section.title {
                text += "## \(title)\n\n" // Markdown for section title
            }
            text += section.content
            return text
        }.joined(separator: "\n\n---\n\n") // Separate sections with a horizontal rule

        return markdownGenerator.generateHomebreweryMarkdown(from: combinedText)
    }
}

// MARK: - ObservableObject Protocol Support
#if canImport(Combine)
public protocol ObservableObjectProtocol: ObservableObject {}
#else
public protocol ObservableObjectProtocol: AnyObject {}
#endif