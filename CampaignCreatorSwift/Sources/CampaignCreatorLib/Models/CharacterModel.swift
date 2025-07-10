import Foundation

// Corresponds to TypeScript 'CharacterStats'
public struct CharacterStats: Codable, Sendable {
    public var strength: Int?
    public var dexterity: Int?
    public var constitution: Int?
    public var intelligence: Int?
    public var wisdom: Int?
    public var charisma: Int?

    // Explicit CodingKeys for CharacterStats to be absolutely sure
    enum CodingKeys: String, CodingKey {
        case strength
        case dexterity
        case constitution
        case intelligence
        case wisdom
        case charisma
    }

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

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case appearanceDescription = "appearance_description"
        case imageURLs = "image_urls"
        case notesForLLM = "notes_for_llm"
        case stats
        case exportFormatPreference = "export_format_preference"
        case createdAt = "created_at"
        case modifiedAt = "modified_at"
        // owner_id is in the JSON but not in the Swift struct, so it's not included here.
        // If it were needed in the struct, it would be: case ownerId = "owner_id"
    }

    }

    // Custom init(from decoder: Decoder) for detailed field-by-field debugging
    public init(from decoder: Decoder) throws {
        let rawDataUserInfoKey = CodingUserInfoKey(rawValue: "rawData")!
        guard let rawData = decoder.userInfo[rawDataUserInfoKey] as? Data else {
            throw DecodingError.dataCorrupted(DecodingError.Context(codingPath: [], debugDescription: "Raw data not found in userInfo"))
        }

        var rawFields: [String: Any] = [:]
        do {
            if let jsonObject = try JSONSerialization.jsonObject(with: rawData, options: []) as? [String: Any] {
                rawFields = jsonObject
                print("[CharacterModel DEBUG init] Successfully parsed rawData with JSONSerialization. Keys: \(rawFields.keys.sorted())")
            } else {
                print("[CharacterModel DEBUG init] Failed to cast JSONSerialization result to [String: Any].")
            }
        } catch {
            print("[CharacterModel DEBUG init] Error parsing rawData with JSONSerialization: \(error.localizedDescription)")
            // Continue, container might still work or fail gracefully.
        }

        print("[CharacterModel DEBUG init] --- Starting Field-by-Field Decoding ---")
        let container = try decoder.container(keyedBy: CodingKeys.self)

        // Helper to print and decode
        func debugDecode<T: Decodable>(_ key: CodingKeys, type: T.Type, isOptional: Bool) throws -> T? {
            print("  [Field: \(key.rawValue)]")
            if let rawValue = rawFields[key.rawValue] {
                print("    JSONSerialization found: \(rawValue) (Type: \(Swift.type(of: rawValue)))")
            } else {
                print("    JSONSerialization: Key '\(key.rawValue)' not found.")
            }

            do {
                if isOptional {
                    let value = try container.decodeIfPresent(T.self, forKey: key)
                    print("    Codable decodeIfPresent: \(value.map { String(describing: $0) } ?? "nil")")
                    return value
                } else {
                    let value = try container.decode(T.self, forKey: key)
                    print("    Codable decode: \(value)")
                    return value
                }
            } catch let error as DecodingError {
                print("    Codable decode ERROR for key '\(key.rawValue)': \(error)")
                // Log more detail from DecodingError
                switch error {
                case .typeMismatch(let type, let context):
                    print("      TypeMismatch: Expected \(type), Path: \(context.codingPath.map(\.stringValue).joined(separator: ".")), Debug: \(context.debugDescription)")
                case .valueNotFound(let type, let context):
                    print("      ValueNotFound: Expected \(type), Path: \(context.codingPath.map(\.stringValue).joined(separator: ".")), Debug: \(context.debugDescription)")
                case .keyNotFound(let actualKey, let context):
                    print("      KeyNotFound: Missing key \(actualKey.stringValue), Path: \(context.codingPath.map(\.stringValue).joined(separator: ".")), Debug: \(context.debugDescription)")
                case .dataCorrupted(let context):
                    print("      DataCorrupted: Path: \(context.codingPath.map(\.stringValue).joined(separator: ".")), Debug: \(context.debugDescription)")
                @unknown default:
                    print("      Unknown DecodingError.")
                }
                if isOptional { return nil } else { throw error }
            } catch {
                 print("    Codable decode UNKNOWN ERROR for key '\(key.rawValue)': \(error.localizedDescription)")
                 if isOptional { return nil } else { throw error }
            }
        }

        // Decoding each field
        self.id = try debugDecode(.id, type: Int.self, isOptional: false)! // Non-optional
        self.name = try debugDecode(.name, type: String.self, isOptional: false)! // Non-optional
        self.description = try debugDecode(.description, type: String.self, isOptional: true)
        self.appearanceDescription = try debugDecode(.appearanceDescription, type: String.self, isOptional: true)
        self.imageURLs = try debugDecode(.imageURLs, type: [String].self, isOptional: true)
        self.notesForLLM = try debugDecode(.notesForLLM, type: String.self, isOptional: true)
        self.stats = try debugDecode(.stats, type: CharacterStats.self, isOptional: true)
        self.exportFormatPreference = try debugDecode(.exportFormatPreference, type: String.self, isOptional: true)
        self.createdAt = try debugDecode(.createdAt, type: Date.self, isOptional: true)
        self.modifiedAt = try debugDecode(.modifiedAt, type: Date.self, isOptional: true)

        print("[CharacterModel DEBUG init] --- Finished Field-by-Field Decoding ---")
        print("[CharacterModel DEBUG init] Final decoded values: id=\(id), name='\(name)', notes='\(notesForLLM ?? "nil")', appearance='\(appearanceDescription ?? "nil")', images=\(imageURLs ?? [])")
    }

    // Memberwise initializer - keep for non-Codable instantiation if needed, or for tests/previews
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
