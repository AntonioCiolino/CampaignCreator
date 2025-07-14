import Foundation

public struct Token: Codable {
    public let access_token: String
    public let token_type: String

    public init(access_token: String, token_type: String) {
        self.access_token = access_token
        self.token_type = token_type
    }
}

public struct TokenData: Codable {
    public let username: String?

    public init(username: String?) {
        self.username = username
    }
}
