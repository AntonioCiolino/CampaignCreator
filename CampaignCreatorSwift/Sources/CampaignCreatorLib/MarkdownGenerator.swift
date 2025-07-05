import Foundation

public struct MarkdownGenerator {
    
    public init() {}

    /// Prepares text for Homebrewery by ensuring user-typed Markdown and specific markers are preserved.
    ///
    /// Currently, this function primarily acts as a passthrough for the user's text,
    /// as users are expected to write full Markdown syntax directly in the editor,
    /// including Homebrewery-specific markers like `\page` and `\column`.
    ///
    /// Standard Markdown syntax (headings, bold, italics, lists, blockquotes, code blocks)
    /// and any HTML/CSS tags typed by the user will be preserved as part of the input string.
    ///
    /// - Parameter plainText: The raw text content from the editor, expected to contain
    ///   Markdown syntax and custom markers.
    /// - Returns: The input text, ready for Homebrewery.
    public func generateHomebreweryMarkdown(from plainText: String) -> String {
        // For this version, the core principle is "what you type is what you get."
        // The user is responsible for correct Markdown and Homebrewery markers.
        
        // No specific conversion is done to `\page` or `\column` here,
        // as the requirement is to pass them through. Homebrewery's actual syntax
        // for these might be more complex (e.g., `{{page}}`, `<div class='pageNumber auto'></div>`, etc.),
        // but the user is typing their chosen marker (`\page`, `\column`) directly.
        
        // If specific conversions were required, they would happen here. For example:
        // var processedText = plainText
        // processedText = processedText.replacingOccurrences(of: "\\page", with: "<div style='page-break-after:always;'></div>")
        // processedText = processedText.replacingOccurrences(of: "\\column", with: "<div style='column-break-after:always;'></div>")
        // However, the current directive is to pass through user's markers.

        return plainText
    }
    
    /// Converts basic text formatting to Markdown
    public func convertToMarkdown(from plainText: String) -> String {
        var markdown = plainText
        
        // Basic conversions - this could be expanded based on needs
        // For now, just ensure proper line breaks
        markdown = markdown.replacingOccurrences(of: "\r\n", with: "\n")
        markdown = markdown.replacingOccurrences(of: "\r", with: "\n")
        
        return markdown
    }
    
    /// Extracts headings from markdown text
    public func extractHeadings(from markdown: String) -> [String] {
        let lines = markdown.components(separatedBy: .newlines)
        return lines.compactMap { line in
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if trimmed.hasPrefix("#") {
                return trimmed
            }
            return nil
        }
    }
}