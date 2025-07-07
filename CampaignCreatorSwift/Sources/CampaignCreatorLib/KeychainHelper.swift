import Foundation
import Security

public struct KeychainHelper {

    public static let service = "com.example.CampaignCreatorApp.Login" // Unique service name for your app

    public enum KeychainError: Error, LocalizedError {
        case saveError(OSStatus)
        case loadError(OSStatus)
        case deleteError(OSStatus)
        case dataConversionError
        case itemNotFound

        public var errorDescription: String? { // Made public
            switch self {
            case .saveError(let status): return "Could not save item to Keychain: \(status)"
            case .loadError(let status): return "Could not load item from Keychain: \(status)"
            case .deleteError(let status): return "Could not delete item from Keychain: \(status)"
            case .dataConversionError: return "Could not convert data for Keychain operation."
            case .itemNotFound: return "Item not found in Keychain."
            }
        }
    }

    // This internal save can remain internal if only used by public savePassword
    internal static func save(username: String, passwordData: Data) throws {
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

    // This internal load can remain internal if only used by public loadPassword
    internal static func load(username: String) throws -> Data {
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

    public static func delete(username: String) throws { // Already public
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
    public static func savePassword(username: String, password string: String) throws { // Already public
        guard let passwordData = string.data(using: .utf8) else {
            throw KeychainError.dataConversionError
        }
        try save(username: username, passwordData: passwordData) // Calls internal save
    }

    public static func loadPassword(username: String) throws -> String { // Already public
        let passwordData = try load(username: username) // Calls internal load
        guard let passwordString = String(data: passwordData, encoding: .utf8) else {
            throw KeychainError.dataConversionError
        }
        return passwordString
    }
}
