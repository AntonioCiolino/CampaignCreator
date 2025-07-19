import Foundation

@objc(StringArrayTransformer)
final class StringArrayTransformer: NSSecureUnarchiveFromDataTransformer {
    static let name = NSValueTransformerName(rawValue: String(describing: StringArrayTransformer.self))

    override static var allowedTopLevelClasses: [AnyClass] {
        return [NSArray.self]
    }

    public static func register() {
        let transformer = StringArrayTransformer()
        ValueTransformer.setValueTransformer(transformer, forName: name)
    }
}
