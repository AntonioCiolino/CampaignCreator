import Foundation

struct Document: Identifiable { // Identifiable can be useful later
    var id = UUID()
    var text: String = "" // Basic property for text content
    var fileURL: URL? // Optional: if you want to associate it with a URL

    // Initialize with text
    init(text: String, fileURL: URL? = nil) {
        self.text = text
        self.fileURL = fileURL
    }

    // Initialize from a URL (example of how it could be used)
    init?(fromURL url: URL) {
        guard let data = try? Data(contentsOf: url),
              let fileText = String(data: data, encoding: .utf8) else {
            return nil
        }
        self.text = fileText
        self.fileURL = url
    }
}
