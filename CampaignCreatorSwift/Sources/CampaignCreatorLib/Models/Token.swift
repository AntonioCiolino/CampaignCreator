import Foundation

public struct Token: Codable, Sendable {
    public let accessToken: String
    public let tokenType: String

    public init(accessToken: String, tokenType: String) {
        self.accessToken = accessToken
        self.tokenType = tokenType
    }
}

public struct TokenData: Codable {
    public let username: String?

    public init(username: String?) {
        self.username = username
    }
}
