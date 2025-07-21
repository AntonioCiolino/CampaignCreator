import Foundation

public protocol TokenManaging: Sendable {
    func getAccessToken() -> String?
    func setAccessToken(_ token: String?)
    func getRefreshToken(for username: String) -> String?
    func setRefreshToken(_ token: String?, for username: String)
    func clearTokens(for username: String)
    func hasToken() -> Bool
}

public final class TokenManager: TokenManaging, Sendable {
    private let accessTokenKey = "AuthAccessToken"

    public func getAccessToken() -> String? {
        return UserDefaults.standard.string(forKey: accessTokenKey)
    }

    public func setAccessToken(_ token: String?) {
        if let token = token {
            UserDefaults.standard.set(token, forKey: accessTokenKey)
        } else {
            UserDefaults.standard.removeObject(forKey: accessTokenKey)
        }
    }

    private func refreshTokenKey(for username: String) -> String {
        return "refreshToken_\(username)"
    }

    public func getRefreshToken(for username: String) -> String? {
        return try? KeychainHelper.loadPassword(username: refreshTokenKey(for: username))
    }

    public func setRefreshToken(_ token: String?, for username: String) {
        let key = refreshTokenKey(for: username)
        if let token = token {
            try? KeychainHelper.savePassword(username: key, password: token)
        } else {
            try? KeychainHelper.delete(username: key)
        }
    }

    public func clearTokens(for username: String) {
        UserDefaults.standard.removeObject(forKey: accessTokenKey)
        try? KeychainHelper.delete(username: refreshTokenKey(for: username))
    }

    public func hasToken() -> Bool {
        return getAccessToken() != nil
    }

    public init() {}
}
