import Foundation

public protocol TokenManaging: Sendable {
    func getAccessToken() -> String?
    func setAccessToken(_ token: String?)
    func getRefreshToken() -> String?
    func setRefreshToken(_ token: String?, for username: String)
    func clearTokens(for username: String)
    func getUsername() -> String?
    func hasToken() -> Bool
}

public final class TokenManager: TokenManaging, Sendable {
    private let accessTokenKey = "AuthAccessToken"
    private let usernameKey = "AuthUsername"

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

    public func getRefreshToken() -> String? {
        guard let username = getUsername() else { return nil }
        return try? KeychainHelper.loadPassword(username: refreshTokenKey(for: username))
    }

    public func setRefreshToken(_ token: String?, for username: String) {
        let key = refreshTokenKey(for: username)
        if let token = token {
            try? KeychainHelper.savePassword(username: key, password: token)
            UserDefaults.standard.set(username, forKey: usernameKey)
        } else {
            try? KeychainHelper.delete(username: key)
            UserDefaults.standard.removeObject(forKey: usernameKey)
        }
    }

    public func clearTokens(for username: String) {
        try? KeychainHelper.delete(username: refreshTokenKey(for: username))
        UserDefaults.standard.removeObject(forKey: accessTokenKey)
        UserDefaults.standard.removeObject(forKey: usernameKey)
    }

    public func getUsername() -> String? {
        return UserDefaults.standard.string(forKey: usernameKey)
    }

    public func hasToken() -> Bool {
        return getAccessToken() != nil
    }

    public init() {}
}
