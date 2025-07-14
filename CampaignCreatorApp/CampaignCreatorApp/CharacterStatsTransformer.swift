import Foundation

class CharacterStatsTransformer: ValueTransformer {
    override class func transformedValueClass() -> AnyClass {
        return NSData.self
    }

    override class func allowsReverseTransformation() -> Bool {
        return true
    }

    override func transformedValue(_ value: Any?) -> Any? {
        guard let stats = value as? CharacterStats else { return nil }

        do {
            let data = try JSONEncoder().encode(stats)
            return data
        } catch {
            print("Failed to encode CharacterStats: \(error)")
            return nil
        }
    }

    override func reverseTransformedValue(_ value: Any?) -> Any? {
        guard let data = value as? Data else { return nil }

        do {
            let stats = try JSONDecoder().decode(CharacterStats.self, from: data)
            return stats
        } catch {
            print("Failed to decode CharacterStats: \(error)")
            return nil
        }
    }
}
