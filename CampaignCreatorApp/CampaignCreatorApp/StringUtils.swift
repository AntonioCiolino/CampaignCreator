import Foundation

extension String {
    /// Removes the given suffix from the string, if it exists.
    /// Otherwise, returns the original string.
    func stripSuffix(_ suffix: String) -> String {
        if self.hasSuffix(suffix) {
            return String(self.dropLast(suffix.count))
        }
        return self
    }

    /// Returns nil if the string is empty after trimming whitespace, otherwise returns the trimmed string.
    func nilIfEmpty() -> String? {
        let trimmed = self.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
