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
    public var id: Int
    public var name: String
    public var description: String?
    public var appearanceDescription: String?
    public var imageURLs: [String]?
    public var notesForLLM: String?
    public var stats: CharacterStats?
    public var exportFormatPreference: String?
    public var createdAt: Date?
    public var modifiedAt: Date?

    enum CodingKeys: String, CodingKey { // Simplified: camelCase, relying on global strategy
        case id
        case name
        case description
        case appearanceDescription
        case imageURLs
        case notesForLLM
        case stats
        case exportFormatPreference
        case createdAt
        case modifiedAt
    }

    // Custom init(from decoder: Decoder) for detailed logging
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        let tempIdForLog = try? container.decode(Int.self, forKey: .id) // For logging before full ID assignment
        print("[DECODE_DEBUG CharacterModel] For ID \(tempIdForLog ?? -99): Attempting to decode. Container allKeys: \(container.allKeys.map { $0.stringValue })")

        id = try container.decode(Int.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        description = try container.decodeIfPresent(String.self, forKey: .description)

        // --- Debugging appearanceDescription ---
        let appearanceKeyExists = container.contains(.appearanceDescription)
        print("[DECODE_DEBUG CharacterModel] For ID \(id): appearanceDescription key exists in JSON (via container.contains): \(appearanceKeyExists)")
        if appearanceKeyExists {
            do {
                let rawAppearance = try container.decode(String.self, forKey: .appearanceDescription)
                print("[DECODE_DEBUG CharacterModel] For ID \(id): appearanceDescription successfully decoded as non-optional String: '\(rawAppearance)'")
                appearanceDescription = rawAppearance
            } catch {
                print("[DECODE_DEBUG CharacterModel] For ID \(id): FAILED to decode appearanceDescription as non-optional String. Error: \(error.localizedDescription). Trying decodeIfPresent...")
                appearanceDescription = try container.decodeIfPresent(String.self, forKey: .appearanceDescription)
            }
        } else {
            print("[DECODE_DEBUG CharacterModel] For ID \(id): appearanceDescription key NOT found by container.contains. Assigning nil.")
            appearanceDescription = nil
        }
        print("[DECODE_DEBUG CharacterModel] For ID \(id): Final appearanceDescription value: '\(appearanceDescription ?? "nil")'")
        // --- End Debugging appearanceDescription ---

        // --- Debugging imageURLs ---
        let imageURLsKeyExists = container.contains(.imageURLs)
        print("[DECODE_DEBUG CharacterModel] For ID \(id): imageURLs key exists in JSON (via container.contains): \(imageURLsKeyExists)")
        if imageURLsKeyExists {
            do {
                let rawImageURLs = try container.decode([String].self, forKey: .imageURLs)
                print("[DECODE_DEBUG CharacterModel] For ID \(id): imageURLs successfully decoded as non-optional [String]: \(rawImageURLs)")
                imageURLs = rawImageURLs
            } catch {
                print("[DECODE_DEBUG CharacterModel] For ID \(id): FAILED to decode imageURLs as non-optional [String]. Error: \(error.localizedDescription). Trying decodeIfPresent...")
                imageURLs = try container.decodeIfPresent([String].self, forKey: .imageURLs)
            }
        } else {
            print("[DECODE_DEBUG CharacterModel] For ID \(id): imageURLs key NOT found by container.contains. Assigning nil.")
            imageURLs = nil
        }
        print("[DECODE_DEBUG CharacterModel] For ID \(id): Final imageURLs value: \(imageURLs ?? [])")
        // --- End Debugging imageURLs ---

        // --- Debugging notesForLLM ---
        let notesKeyExists = container.contains(.notesForLLM)
        print("[DECODE_DEBUG CharacterModel] For ID \(id): notesForLLM key exists in JSON (via container.contains): \(notesKeyExists)")
        if notesKeyExists {
            do {
                let rawNotes = try container.decode(String.self, forKey: .notesForLLM)
                print("[DECODE_DEBUG CharacterModel] For ID \(id): notesForLLM successfully decoded as non-optional String: '\(rawNotes)'")
                notesForLLM = rawNotes
            } catch {
                print("[DECODE_DEBUG CharacterModel] For ID \(id): FAILED to decode notesForLLM as non-optional String. Error: \(error.localizedDescription). Trying decodeIfPresent...")
                notesForLLM = try container.decodeIfPresent(String.self, forKey: .notesForLLM)
            }
        } else {
            print("[DECODE_DEBUG CharacterModel] For ID \(id): notesForLLM key NOT found by container.contains. Assigning nil.")
            notesForLLM = nil
        }
        print("[DECODE_DEBUG CharacterModel] For ID \(id): Final notesForLLM value: '\(notesForLLM ?? "nil")'")
        // --- End Debugging notesForLLM ---

        stats = try container.decodeIfPresent(CharacterStats.self, forKey: .stats)
        exportFormatPreference = try container.decodeIfPresent(String.self, forKey: .exportFormatPreference)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt)
        modifiedAt = try container.decodeIfPresent(Date.self, forKey: .modifiedAt)

        print("[DECODE_DEBUG CharacterModel] For ID \(id): Decoding complete. Final values - appearance: '\(appearanceDescription ?? "nil")', notes: '\(notesForLLM ?? "nil")', images: \(imageURLs ?? [])")
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
