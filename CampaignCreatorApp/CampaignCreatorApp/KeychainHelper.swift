import Foundation
import Security

struct KeychainHelper {

    static let service = "com.example.CampaignCreatorApp.Login" // Unique service name for your app

    enum KeychainError: Error, LocalizedError {
        case saveError(OSStatus)
        case loadError(OSStatus)
        case deleteError(OSStatus)
        case dataConversionError
        case itemNotFound

        var errorDescription: String? {
            switch self {
            case .saveError(let status): return "Could not save item to Keychain: \(status)"
            case .loadError(let status): return "Could not load item from Keychain: \(status)"
            case .deleteError(let status): return "Could not delete item from Keychain: \(status)"
            case .dataConversionError: return "Could not convert data for Keychain operation."
            case .itemNotFound: return "Item not found in Keychain."
            }
        }
    }

    static func save(username: String, passwordData: Data) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: username,
            kSecValueData as String: passwordData
        ]

        // Delete existing item before saving, to prevent duplicates or update issues
        SecItemDelete(query as CFDictionary)

        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.saveError(status)
        }
        print("Keychain: Successfully saved password for username '\(username)'")
    }

    static func load(username: String) throws -> Data {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: username,
            kSecReturnData as String: kCFBooleanTrue!,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var dataTypeRef: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &dataTypeRef)

        guard status != errSecItemNotFound else {
            throw KeychainError.itemNotFound
        }
        guard status == errSecSuccess else {
            throw KeychainError.loadError(status)
        }
        guard let retrievedData = dataTypeRef as? Data else {
            throw KeychainError.dataConversionError
        }
        print("Keychain: Successfully loaded password for username '\(username)'")
        return retrievedData
    }

    static func delete(username: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: username
        ]

        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            // errSecItemNotFound is acceptable for delete if it's already gone
            throw KeychainError.deleteError(status)
        }
        print("Keychain: Successfully deleted/confirmed no password for username '\(username)' (Status: \(status))")
    }

    // Convenience methods for String passwords
    static func savePassword(username: String, password string: String) throws {
        guard let passwordData = string.data(using: .utf8) else {
            throw KeychainError.dataConversionError
        }
        try save(username: username, passwordData: passwordData)
    }

    static func loadPassword(username: String) throws -> String {
        let passwordData = try load(username: username)
        guard let passwordString = String(data: passwordData, encoding: .utf8) else {
            throw KeychainError.dataConversionError
        }
        return passwordString
    }

    static func saveRefreshToken(_ token: String) throws {
        try save(username: "refreshToken", passwordData: token.data(using: .utf8)!)
    }

    static func loadRefreshToken() throws -> String {
        let tokenData = try load(username: "refreshToken")
        guard let token = String(data: tokenData, encoding: .utf8) else {
            throw KeychainError.dataConversionError
        }
        return token
    }

    static func deleteRefreshToken() throws {
        try delete(username: "refreshToken")
    }
}
