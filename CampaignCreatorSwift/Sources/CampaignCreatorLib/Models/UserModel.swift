import Foundation

public struct User: Identifiable, Codable, Equatable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var email: String
    public var username: String? // Or non-optional if always present
    public var isActive: Bool? // Common field from FastAPI users, changed from is_active
    public var isSuperuser: Bool? // Changed from is_superuser
    public var description: String?
    public var appearance: String?
    public var avatarUrl: String? // Changed from avatar_url

    enum CodingKeys: String, CodingKey {
        case id, email, username, description, appearance
        case isActive = "is_active"
        case isSuperuser = "is_superuser"
        case avatarUrl = "avatar_url"
    }

    // Add other fields your /users/me endpoint returns, e.g.:
    // public var fullName: String?
    // public var createdAt: Date?
    // public var modifiedAt: Date?

    public init(id: Int, email: String, username: String? = nil, isActive: Bool? = true, isSuperuser: Bool? = false, description: String? = nil, appearance: String? = nil, avatarUrl: String? = nil) { // Changed id from UUID to Int and avatar_url to avatarUrl, is_active to isActive, is_superuser to isSuperuser
        self.id = id
        self.email = email
        self.username = username
        self.isActive = isActive // Changed from is_active
        self.isSuperuser = isSuperuser // Changed from is_superuser
        self.description = description
        self.appearance = appearance
        self.avatarUrl = avatarUrl // Changed from avatar_url
    }
}
