import Foundation

extension Collection {
    /// Returns `nil` if the collection is empty, otherwise returns the collection itself.
    func nilIfEmpty() -> Self? {
        return isEmpty ? nil : self
    }
}
