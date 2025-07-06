import Foundation

public struct User: Identifiable, Codable, Equatable {
    public var id: UUID // Assuming backend provides UUID for user ID. Adjust if Int.
    public var email: String
    public var username: String? // Or non-optional if always present
    public var is_active: Bool? // Common field from FastAPI users
    public var is_superuser: Bool?

    // Add other fields your /users/me endpoint returns, e.g.:
    // public var fullName: String?
    // public var createdAt: Date?
    // public var modifiedAt: Date?

    public init(id: UUID, email: String, username: String? = nil, is_active: Bool? = true, is_superuser: Bool? = false) {
        self.id = id
        self.email = email
        self.username = username
        self.is_active = is_active
        self.is_superuser = is_superuser
    }
}
