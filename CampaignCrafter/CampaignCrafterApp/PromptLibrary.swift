import Foundation

struct PromptLibrary {
    /// Prompt to generate a campaign concept.
    /// Expects one argument: user input concepts.
    static let generateCampaignConcept = "Create a campaign based on the following concepts: %@###\n\n"

    /// Prompt to generate a table of contents.
    /// Expects one argument: the full campaign text generated so far.
    static let generateTableOfContents = "%@Table of Contents: \n"

    /// Prompt to generate campaign titles.
    /// Expects one argument: the campaign concept.
    static let generateCampaignTitles = "Create a few campaign names for a DnD campaign with %@. Use sensory language and hyperbole and metaphor."

    /// Prompt to continue writing a section.
    /// Expects three arguments:
    /// 1. The overall campaign text.
    /// 2. The table of contents text.
    /// 3. The current chapter text to be continued.
    static let continueSection = "%@###\n\n%@\n\n%@"
}
