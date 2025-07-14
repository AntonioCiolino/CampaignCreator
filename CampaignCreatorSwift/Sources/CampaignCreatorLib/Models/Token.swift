import Foundation

public struct Token: Codable, Sendable {
    public let accessToken: String
    public let tokenType: String

    public init(access_token: String, token_type: String) {
        self.accessToken = access_token
        self.tokenType = token_type
    }
}

public struct TokenData: Codable {
    public let username: String?

    public init(username: String?) {
        self.username = username
    }
}
