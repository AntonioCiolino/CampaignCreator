import Foundation

public struct Token: Codable {
    public let accessToken: String
    public let tokenType: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }

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
