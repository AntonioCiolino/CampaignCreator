import Foundation

// Corresponds to TypeScript 'TOCEntry'
public struct TOCEntry: Identifiable, Codable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var title: String
    public var type: String // e.g., "Introduction", "Chapter 1", "Appendix"

    public init(id: Int, title: String, type: String) { // Changed id from UUID to Int, removed default
        self.id = id
        self.title = title
        self.type = type
    }
}

// New struct for campaign custom sections
public struct CampaignCustomSection: Identifiable, Codable, Sendable, Hashable { // Added Hashable
    public var id: Int // CHANGED from UUID to Int
    public var title: String
    public var content: String
    public var type: String?
    // public var order: Int // Optional: if explicit ordering is needed beyond array order

    public init(id: Int, title: String, content: String, type: String? = "Generic" /*, order: Int = 0*/) { // CHANGED id to Int, made it non-optional in param
        self.id = id
        self.title = title
        self.content = content
        self.type = type
        // self.order = order
    }
}

// Corresponds to TypeScript 'CampaignSection'
public struct CampaignSection: Identifiable, Codable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var title: String?
    public var content: String
    public var order: Int
    // public var campaign_id: UUID // Link back to the Campaign, if sections are stored separately
    public var type: String? // e.g., "Narrative", "Location", "NPC"

    public init(id: Int, title: String? = nil, content: String, order: Int, type: String? = nil) { // Changed id from UUID to Int, removed default
        self.id = id
        self.title = title
        self.content = content
        self.order = order
        self.type = type
    }
}

// This struct will represent the Campaign. We are evolving the old 'Document' into this.
public struct Campaign: Identifiable, Codable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var title: String
    public var initialUserPrompt: String?
    public var concept: String?
    public var displayTOC: [TOCEntry]? // Table of Contents
    public var sections: [CampaignSection] // Campaign sections

    // Metadata from React app's Campaign
    public var badgeImageURL: String?
    public var thematicImageURL: String?
    public var thematicImagePrompt: String?
    public var selectedLLMId: String?
    public var temperature: Double? // Changed from Int to Double for more precision
    public var moodBoardImageURLs: [String]?

    // Theme properties
    public var themePrimaryColor: String?
    public var themeSecondaryColor: String?
    public var themeBackgroundColor: String?
    public var themeTextColor: String?
    public var themeFontFamily: String?
    public var themeBackgroundImageURL: String?
    public var themeBackgroundImageOpacity: Double?

    public var fileURL: URL? // Keep if direct file association is needed for saving/loading whole campaign
    public var createdAt: Date? // Changed to optional
    public var modifiedAt: Date? // Changed to optional

    // Linking characters
    public var linkedCharacterIDs: [Int]? // CHANGED from [UUID]?
    public var customSections: [CampaignCustomSection]? // <<<< ADDED

    // Explicit CodingKeys to handle potential snake_case to camelCase discrepancies if strategy isn't working perfectly
    enum CodingKeys: String, CodingKey {
        case id, title, concept, sections // Standard names, no mapping needed unless backend is different
        case initialUserPrompt = "initial_user_prompt"
        case displayTOC = "display_toc"
        case badgeImageURL = "badge_image_url"
        case thematicImageURL = "thematic_image_url"
        case thematicImagePrompt = "thematic_image_prompt"
        case selectedLLMId = "selected_llm_id"
        case temperature
        case moodBoardImageURLs = "mood_board_image_urls"
        case themePrimaryColor = "theme_primary_color"
        case themeSecondaryColor = "theme_secondary_color"
        case themeBackgroundColor = "theme_background_color"
        case themeTextColor = "theme_text_color"
        case themeFontFamily = "theme_font_family"
        case themeBackgroundImageURL = "theme_background_image_url"
        case themeBackgroundImageOpacity = "theme_background_image_opacity"
        case fileURL // Assuming fileURL is not snake_case from backend, if it is, map it.
        case createdAt = "created_at"
        case modifiedAt = "modified_at"
        case linkedCharacterIDs = "linked_character_ids"
        case customSections = "custom_sections"
        // WordCount is a computed property, not decoded
    }

    // Custom Initializer for Decodable
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(Int.self, forKey: .id)
        title = try container.decode(String.self, forKey: .title)
        initialUserPrompt = try container.decodeIfPresent(String.self, forKey: .initialUserPrompt)
        concept = try container.decodeIfPresent(String.self, forKey: .concept)
        displayTOC = try container.decodeIfPresent([TOCEntry].self, forKey: .displayTOC)
        sections = try container.decode([CampaignSection].self, forKey: .sections)

        print("[Campaign Decodable] --- Aggressive Debug for badgeImageURL ---")
        print("[Campaign Decodable] Checking for key .badgeImageURL using string value '\(CodingKeys.badgeImageURL.stringValue)': \(container.contains(.badgeImageURL))")
        if container.contains(.badgeImageURL) {
            print("[Campaign Decodable] Key .badgeImageURL FOUND.")
            do {
                // Try to decode as non-optional String first to force an error if value is null or wrong type
                let tempBadgeURL = try container.decode(String.self, forKey: .badgeImageURL)
                self.badgeImageURL = tempBadgeURL
                print("[Campaign Decodable] badgeImageURL DECODED SUCCESSFULLY (as non-optional String): \(self.badgeImageURL ?? "nil but shouldn't be")")
            } catch let error as DecodingError {
                print("❗️ [Campaign Decodable] DecodingError for badgeImageURL (when trying non-optional String): \(error)")
                // print("    Context: \(error.localizedDescription)") // localizedDescription might be too generic
                switch error {
                case .typeMismatch(let type, let context):
                    print("    Type Mismatch: Expected String, got \(type). Path: \(context.codingPath.map { $0.stringValue }.joined(separator: ".")), Debug: \(context.debugDescription)")
                    // If type mismatch, try decodeIfPresent as a fallback for logging, though it likely still results in nil
                    self.badgeImageURL = try? container.decodeIfPresent(String.self, forKey: .badgeImageURL)
                    print("    [Campaign Decodable] badgeImageURL after trying decodeIfPresent (following typeMismatch): \(self.badgeImageURL ?? "nil")")
                case .valueNotFound(let type, let context): // This means JSON value was 'null'
                    print("    Value Not Found: Expected String, but JSON value was null for type \(type). Path: \(context.codingPath.map { $0.stringValue }.joined(separator: ".")), Debug: \(context.debugDescription)")
                    // Now try decodeIfPresent as it should handle null by returning nil
                    self.badgeImageURL = try? container.decodeIfPresent(String.self, forKey: .badgeImageURL)
                    print("    [Campaign Decodable] badgeImageURL after trying decodeIfPresent (following valueNotFound): \(self.badgeImageURL ?? "nil")")
                case .keyNotFound(let key, let context): // Should not happen if container.contains was true
                    print("    Key Not Found: \(key.stringValue). Path: \(context.codingPath.map { $0.stringValue }.joined(separator: ".")), Debug: \(context.debugDescription)")
                    self.badgeImageURL = nil
                case .dataCorrupted(let context):
                    print("    Data Corrupted. Path: \(context.codingPath.map { $0.stringValue }.joined(separator: ".")), Debug: \(context.debugDescription)")
                    self.badgeImageURL = nil
                @unknown default:
                    print("    Unknown DecodingError for badgeImageURL.")
                    self.badgeImageURL = nil
                }
            } catch {
                print("❗️ [Campaign Decodable] UNKNOWN non-DecodingError for badgeImageURL: \(error)")
                self.badgeImageURL = nil
            }
        } else {
            print("❗️ [Campaign Decodable] Key .badgeImageURL NOT FOUND in container.")
            self.badgeImageURL = nil
        }
        print("[Campaign Decodable] --- End Aggressive Debug for badgeImageURL ---")

        thematicImageURL = try container.decodeIfPresent(String.self, forKey: .thematicImageURL)
        thematicImagePrompt = try container.decodeIfPresent(String.self, forKey: .thematicImagePrompt)
        selectedLLMId = try container.decodeIfPresent(String.self, forKey: .selectedLLMId)
        temperature = try container.decodeIfPresent(Double.self, forKey: .temperature)

        print("[Campaign Decodable] Checking for key .moodBoardImageURLs: \(CodingKeys.moodBoardImageURLs.stringValue). Key Found in JSON container: \(container.contains(.moodBoardImageURLs))")
        do {
            moodBoardImageURLs = try container.decodeIfPresent([String].self, forKey: .moodBoardImageURLs)
            print("[Campaign Decodable] moodBoardImageURLs successfully decoded (or was nil in JSON): \(moodBoardImageURLs?.joined(separator: ", ") ?? "nil")")
        } catch let error as DecodingError {
            print("❗️ [Campaign Decodable] DecodingError for moodBoardImageURLs: \(error) - Key: \(CodingKeys.moodBoardImageURLs.stringValue)")
            moodBoardImageURLs = nil
        } catch {
            print("❗️ [Campaign Decodable] UNKNOWN error decoding moodBoardImageURLs: \(error) - Key: \(CodingKeys.moodBoardImageURLs.stringValue)")
            moodBoardImageURLs = nil
        }

        themePrimaryColor = try container.decodeIfPresent(String.self, forKey: .themePrimaryColor)
        themeSecondaryColor = try container.decodeIfPresent(String.self, forKey: .themeSecondaryColor)
        themeBackgroundColor = try container.decodeIfPresent(String.self, forKey: .themeBackgroundColor)
        themeTextColor = try container.decodeIfPresent(String.self, forKey: .themeTextColor)
        themeFontFamily = try container.decodeIfPresent(String.self, forKey: .themeFontFamily)
        themeBackgroundImageURL = try container.decodeIfPresent(String.self, forKey: .themeBackgroundImageURL)
        themeBackgroundImageOpacity = try container.decodeIfPresent(Double.self, forKey: .themeBackgroundImageOpacity)

        fileURL = try container.decodeIfPresent(URL.self, forKey: .fileURL) // URL might need special handling if it's just a string in JSON
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt)
        modifiedAt = try container.decodeIfPresent(Date.self, forKey: .modifiedAt)

        linkedCharacterIDs = try container.decodeIfPresent([Int].self, forKey: .linkedCharacterIDs)
        customSections = try container.decodeIfPresent([CampaignCustomSection].self, forKey: .customSections)
    }

    // Custom Encoder for Encodable
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(title, forKey: .title)
        try container.encodeIfPresent(initialUserPrompt, forKey: .initialUserPrompt)
        try container.encodeIfPresent(concept, forKey: .concept)
        try container.encodeIfPresent(displayTOC, forKey: .displayTOC)
        try container.encode(sections, forKey: .sections)

        try container.encodeIfPresent(badgeImageURL, forKey: .badgeImageURL)
        print("[Campaign Encodable] Attempting to encode badgeImageURL: \(badgeImageURL ?? "nil")")

        try container.encodeIfPresent(thematicImageURL, forKey: .thematicImageURL)
        try container.encodeIfPresent(thematicImagePrompt, forKey: .thematicImagePrompt)
        try container.encodeIfPresent(selectedLLMId, forKey: .selectedLLMId)
        try container.encodeIfPresent(temperature, forKey: .temperature)

        try container.encodeIfPresent(moodBoardImageURLs, forKey: .moodBoardImageURLs)
        print("[Campaign Encodable] Attempting to encode moodBoardImageURLs: \(moodBoardImageURLs?.joined(separator: ", ") ?? "nil")")

        try container.encodeIfPresent(themePrimaryColor, forKey: .themePrimaryColor)
        try container.encodeIfPresent(themeSecondaryColor, forKey: .themeSecondaryColor)
        try container.encodeIfPresent(themeBackgroundColor, forKey: .themeBackgroundColor)
        try container.encodeIfPresent(themeTextColor, forKey: .themeTextColor)
        try container.encodeIfPresent(themeFontFamily, forKey: .themeFontFamily)
        try container.encodeIfPresent(themeBackgroundImageURL, forKey: .themeBackgroundImageURL)
        try container.encodeIfPresent(themeBackgroundImageOpacity, forKey: .themeBackgroundImageOpacity)

        try container.encodeIfPresent(fileURL, forKey: .fileURL)
        try container.encodeIfPresent(createdAt, forKey: .createdAt)
        try container.encodeIfPresent(modifiedAt, forKey: .modifiedAt)

        try container.encodeIfPresent(linkedCharacterIDs, forKey: .linkedCharacterIDs)
        try container.encodeIfPresent(customSections, forKey: .customSections)
    }

    // Existing memberwise initializer - keep it for programmatic creation
    public init(id: Int,
                title: String = "Untitled Campaign",
                initialUserPrompt: String? = nil,
                concept: String? = nil,
                displayTOC: [TOCEntry]? = nil,
                sections: [CampaignSection] = [],
                badgeImageURL: String? = nil,
                thematicImageURL: String? = nil,
                thematicImagePrompt: String? = nil,
                selectedLLMId: String? = nil,
                temperature: Double? = 0.7,
                moodBoardImageURLs: [String]? = nil,
                themePrimaryColor: String? = nil,
                themeSecondaryColor: String? = nil,
                themeBackgroundColor: String? = nil,
                themeTextColor: String? = nil,
                themeFontFamily: String? = nil,
                themeBackgroundImageURL: String? = nil,
                themeBackgroundImageOpacity: Double? = nil,
                fileURL: URL? = nil,
                createdAt: Date? = nil, // Changed to optional, default nil
                modifiedAt: Date? = nil, // Changed to optional, default nil
                linkedCharacterIDs: [Int]? = nil, // CHANGED from [UUID]?
                customSections: [CampaignCustomSection]? = nil) { // <<<< ADDED
        self.id = id
        self.title = title
        self.initialUserPrompt = initialUserPrompt
        self.concept = concept
        self.displayTOC = displayTOC
        self.sections = sections
        self.badgeImageURL = badgeImageURL
        self.thematicImageURL = thematicImageURL
        self.thematicImagePrompt = thematicImagePrompt
        self.selectedLLMId = selectedLLMId
        self.temperature = temperature
        self.moodBoardImageURLs = moodBoardImageURLs
        self.themePrimaryColor = themePrimaryColor
        self.themeSecondaryColor = themeSecondaryColor
        self.themeBackgroundColor = themeBackgroundColor
        self.themeTextColor = themeTextColor
        self.themeFontFamily = themeFontFamily
        self.themeBackgroundImageURL = themeBackgroundImageURL
        self.themeBackgroundImageOpacity = themeBackgroundImageOpacity
        self.fileURL = fileURL
        self.createdAt = createdAt
        self.modifiedAt = modifiedAt
        self.linkedCharacterIDs = linkedCharacterIDs
        self.customSections = customSections // <<<< ADDED
    }

    // Word count can be a computed property, summing word counts of all sections
    public var wordCount: Int {
        sections.reduce(0) { $0 + $1.content.components(separatedBy: .whitespacesAndNewlines).filter { !$0.isEmpty }.count }
    }

    // Convenience to update modification time
    public mutating func markAsModified() {
        self.modifiedAt = Date()
    }

    // Placeholder for save/load logic if we treat the whole Campaign as one JSON file
    public func save(to url: URL) throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(self)
        try data.write(to: url, options: .atomic)
    }

    public static func load(from url: URL) throws -> Campaign {
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(Campaign.self, from: data)
    }
}
