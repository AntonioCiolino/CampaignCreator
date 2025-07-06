import Foundation

public struct User: Identifiable, Codable, Equatable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var email: String
    public var username: String? // Or non-optional if always present
    public var is_active: Bool? // Common field from FastAPI users
    public var is_superuser: Bool?

    // Add other fields your /users/me endpoint returns, e.g.:
    // public var fullName: String?
    // public var createdAt: Date?
    // public var modifiedAt: Date?

    public init(id: Int, email: String, username: String? = nil, is_active: Bool? = true, is_superuser: Bool? = false) { // Changed id from UUID to Int
        self.id = id
        self.email = email
        self.username = username
        self.is_active = is_active
        self.is_superuser = is_superuser
    }
}
