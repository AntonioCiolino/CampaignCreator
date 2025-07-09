import Foundation

// Corresponds to TypeScript 'CharacterStats'
public struct CharacterStats: Codable, Sendable {
    public var strength: Int?
    public var dexterity: Int?
    public var constitution: Int?
    public var intelligence: Int?
    public var wisdom: Int?
    public var charisma: Int?

    public init(strength: Int? = nil, dexterity: Int? = nil, constitution: Int? = nil,
                intelligence: Int? = nil, wisdom: Int? = nil, charisma: Int? = nil) {
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
    }
}

// Corresponds to TypeScript 'Character'
public struct Character: Identifiable, Codable, Sendable {
    public var id: Int // Changed from UUID to Int
    // public var ownerId: UUID? // If we need to associate with a user someday
    public var name: String
    public var description: String?
    public var appearanceDescription: String?
    public var imageURLs: [String]?
    public var notesForLLM: String?
    public var stats: CharacterStats?
    public var exportFormatPreference: String? // e.g., "JSON", "Markdown"

    // Metadata
    public var createdAt: Date? // Changed to optional
    public var modifiedAt: Date? // Changed to optional
    // public var customSections: [CustomSection]? // REMOVED

    enum CodingKeys: String, CodingKey { // Or just `enum CodingKeys: CodingKey` if some conventions allow omitting String
        case id
        case name
        case description
        case appearanceDescription // Rely on global strategy
        case imageURLs             // Rely on global strategy
        case notesForLLM           // Rely on global strategy
        case stats
        case exportFormatPreference// Rely on global strategy
        case createdAt             // Rely on global strategy
        case modifiedAt            // Rely on global strategy
    }

    // Custom init(from decoder: Decoder) for detailed logging
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        // Log all keys recognized by the container
        let tempIdForLog = try? container.decode(Int.self, forKey: .id)
        print("[DECODE_DEBUG CharacterModel] For ID \(tempIdForLog ?? -99): Container allKeys: \(container.allKeys.map { $0.stringValue })")

        id = try container.decode(Int.self, forKey: .id) // Re-decode id for assignment or use tempIdForLog if it's guaranteed to be called first
        name = try container.decode(String.self, forKey: .name)
        description = try container.decodeIfPresent(String.self, forKey: .description)

        // --- Debugging appearanceDescription ---
        let appearanceKeyExists = container.contains(.appearanceDescription)
        print("[DECODE_DEBUG CharacterModel] For ID \(id): appearanceDescription key exists in JSON: \(appearanceKeyExists)")
        if appearanceKeyExists {
            do {
                let rawAppearance = try container.decode(String.self, forKey: .appearanceDescription)
                print("[DECODE_DEBUG CharacterModel] For ID \(id): appearanceDescription successfully decoded as non-optional String: '\(rawAppearance)'")
                appearanceDescription = rawAppearance // Assign if successfully decoded as non-optional
            } catch {
                print("[DECODE_DEBUG CharacterModel] For ID \(id): FAILED to decode appearanceDescription as non-optional String. Error: \(error.localizedDescription). Trying decodeIfPresent...")
                appearanceDescription = try container.decodeIfPresent(String.self, forKey: .appearanceDescription)
            }
        } else {
            appearanceDescription = nil // Key doesn't exist, so it's nil
        }
        print("[DECODE_DEBUG CharacterModel] For ID \(id): Final appearanceDescription value: '\(appearanceDescription ?? "nil")'")
        // --- End Debugging appearanceDescription ---

        // --- Debugging imageURLs ---
        let imageURLsKeyExists = container.contains(.imageURLs)
        print("[DECODE_DEBUG CharacterModel] For ID \(id): imageURLs key exists in JSON: \(imageURLsKeyExists)")
        if imageURLsKeyExists {
            do {
                let rawImageURLs = try container.decode([String].self, forKey: .imageURLs)
                print("[DECODE_DEBUG CharacterModel] For ID \(id): imageURLs successfully decoded as non-optional [String]: '\(rawImageURLs)'")
                imageURLs = rawImageURLs
            } catch {
                print("[DECODE_DEBUG CharacterModel] For ID \(id): FAILED to decode imageURLs as non-optional [String]. Error: \(error.localizedDescription). Trying decodeIfPresent...")
                imageURLs = try container.decodeIfPresent([String].self, forKey: .imageURLs)
            }
        } else {
            imageURLs = nil // Key doesn't exist, so it's nil
        }
        print("[DECODE_DEBUG CharacterModel] For ID \(id): Final imageURLs value: \(imageURLs ?? [])") // Print empty array if nil for clarity
        // --- End Debugging imageURLs ---

        // --- Debugging notesForLLM ---
        let notesKeyExists = container.contains(.notesForLLM)
        print("[DECODE_DEBUG CharacterModel] For ID \(id): notesForLLM key exists in JSON: \(notesKeyExists)")
        if notesKeyExists {
            do {
                let rawNotes = try container.decode(String.self, forKey: .notesForLLM)
                print("[DECODE_DEBUG CharacterModel] For ID \(id): notesForLLM successfully decoded as non-optional String: '\(rawNotes)'")
                notesForLLM = rawNotes // Assign if successfully decoded as non-optional
            } catch {
                print("[DECODE_DEBUG CharacterModel] For ID \(id): FAILED to decode notesForLLM as non-optional String. Error: \(error.localizedDescription). Trying decodeIfPresent...")
                notesForLLM = try container.decodeIfPresent(String.self, forKey: .notesForLLM)
            }
        } else {
            notesForLLM = nil // Key doesn't exist, so it's nil
        }
        print("[DECODE_DEBUG CharacterModel] For ID \(id): Final notesForLLM value: '\(notesForLLM ?? "nil")'")
        // --- End Debugging notesForLLM ---

        stats = try container.decodeIfPresent(CharacterStats.self, forKey: .stats)
        exportFormatPreference = try container.decodeIfPresent(String.self, forKey: .exportFormatPreference)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt)
        modifiedAt = try container.decodeIfPresent(Date.self, forKey: .modifiedAt)
    }

    // Original memberwise initializer - keep for non-Codable instantiation if needed, or for tests
    public init(id: Int,
                name: String,
                description: String? = nil,
                appearanceDescription: String? = nil,
                imageURLs: [String]? = nil,
                notesForLLM: String? = nil,
                stats: CharacterStats? = nil,
                exportFormatPreference: String? = nil,
                createdAt: Date? = nil,
                modifiedAt: Date? = nil) {
        self.id = id
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
        self.createdAt = createdAt
        self.modifiedAt = modifiedAt
    }

    // Convenience to update modification time
    public mutating func markAsModified() {
        self.modifiedAt = Date()
    }
}

// CustomSection struct REMOVED from here (will be added to CampaignModel.swift)
