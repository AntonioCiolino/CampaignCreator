import Foundation

public struct Document: Identifiable, Codable {
    public var id = UUID()
    public var text: String = ""
    public var fileURL: URL?
    public var title: String
    public var createdAt: Date
    public var modifiedAt: Date

    // Initialize with text
    public init(text: String = "", title: String = "Untitled Document", fileURL: URL? = nil) {
        self.text = text
        self.title = title
        self.fileURL = fileURL
        self.createdAt = Date()
        self.modifiedAt = Date()
    }

    // Initialize from a URL
    public init?(fromURL url: URL) {
        guard let data = try? Data(contentsOf: url),
              let fileText = String(data: data, encoding: .utf8) else {
            return nil
        }
        self.text = fileText
        self.title = url.deletingPathExtension().lastPathComponent
        self.fileURL = url
        self.createdAt = Date()
        self.modifiedAt = Date()
    }
    
    // Update modification time when text changes
    public mutating func updateText(_ newText: String) {
        self.text = newText
        self.modifiedAt = Date()
    }
    
    // Save document to file
    public func save(to url: URL) throws {
        try text.write(to: url, atomically: true, encoding: .utf8)
    }
    
    // Get file size
    public var size: Int {
        return text.utf8.count
    }
    
    // Get word count
    public var wordCount: Int {
        return text.components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }
            .count
    }
}