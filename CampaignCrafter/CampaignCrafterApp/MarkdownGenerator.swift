import Foundation

struct MarkdownGenerator {

    static let titlePageStyle = """
    <style>
      .phb#p1{ text-align:center; }
      .phb#p1:after{ display:none; }
    </style>
    """

    static let pageImage = """
    {{background,image,bottom,left,50%
    <img 
      src='https://www.gmbinder.com/images/8ENpL1C.png'
      style='position:absolute;bottom:0px;left:0px;width:100%;z-index:-1' />
    }}
    """

    static let pageStain = """
    {{stain,wide
    ![](https://www.gmbinder.com/images/hCVHD2P.png)
    }}
    """

    // Expects: 1. campaignTitle, 2. conceptHeader
    static let pageHeaderTemplate = """
    {{page,number,auto}}
    {{footnote,%1$@}}
    {{note,wide
    ##### Campaign Concept: %2$@
    }}
    ::
    """

    private static func processBlock(content: String, prefix: String, suffix: String) -> String {
        var processedLines: [String] = []
        let lines = content.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)

        for line in lines {
            var processedLine = line
            if line.count > 2 && line[line.index(line.startIndex, offsetBy: 1)] == "." && line[line.index(line.startIndex, offsetBy: 2)] == " " {
                if let digit = Int(String(line.first!)) { // Check if the first char is a digit
                    if digit >= 1 && digit <= 9 {
                        let textAfterNumber = String(line.dropFirst(3))
                        processedLine = String(format: prefix, String(digit)) + textAfterNumber + suffix
                    }
                }
            }
            processedLines.append(processedLine)
        }
        return processedLines.joined(separator: "\n")
    }

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
    func generateHomebreweryMarkdown(mainContent: String, campaignTitle: String, conceptHeader: String, tableOfContentsRaw: String) -> String {
        
        // Process mainContent (chapters)
        var processedChapterText = mainContent
        processedChapterText = processedChapterText.replacingOccurrences(of: "Background:", with: ":\n###  Background\n")
        processedChapterText = MarkdownGenerator.processBlock(content: processedChapterText, prefix: "### %@. ", suffix: "\n")

        // Process Table of Contents
        var processedTocText = tableOfContentsRaw
        if !tableOfContentsRaw.isEmpty {
            let tocTitleReplacement = String(format: "# Table of Contents\n- ### {{ %@ }}{{ }}\n", campaignTitle)
            processedTocText = processedTocText.replacingOccurrences(of: "Table of Contents:", with: tocTitleReplacement)
            processedTocText = processedTocText.replacingOccurrences(of: "\\n", with: "\n") // Ensure literal \n are newlines
            processedTocText = MarkdownGenerator.processBlock(content: processedTocText, prefix: "\t- ####  {{{{  %@. ", suffix: " }}{{ 0}}\n")
        } else {
            // Create a basic ToC if none provided, as the template expects something for the ToC block
            processedTocText = String(format: "# Table of Contents\n- ### {{ %@ }}{{ }}\n", campaignTitle)
        }

        // Assemble the final output
        var output = ""
        output += String(format: MarkdownGenerator.pageHeaderTemplate, campaignTitle, conceptHeader)
        output += MarkdownGenerator.titlePageStyle + "\n"
        output += MarkdownGenerator.pageImage + "\n"
        output += MarkdownGenerator.pageStain + "\n"
        output += "\\page\n" // Homebrewery page break
        output += "{{pageNumber,auto}}\n"
        output += String(format: "{{footnote | %@ }}\n", campaignTitle)
        output += String(format: "{{note,wide\n##### Campaign Concept: %@\n}}\n::\n", conceptHeader)
        output += String(format: "{{toc,wide\n%@}}\n::\n", processedTocText)
        output += "\n\n## Campaign\n\n"
        output += processedChapterText

        return output
    }
}
