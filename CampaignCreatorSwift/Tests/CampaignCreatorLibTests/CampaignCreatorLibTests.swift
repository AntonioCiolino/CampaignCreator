import XCTest
@testable import CampaignCreatorLib

final class CampaignCreatorLibTests: XCTestCase {
    
    func testDocumentCreation() {
        let document = Document(text: "Test content", title: "Test Document")
        
        XCTAssertEqual(document.title, "Test Document")
        XCTAssertEqual(document.text, "Test content")
        XCTAssertEqual(document.wordCount, 2)
        XCTAssertEqual(document.size, 12)
        XCTAssertNotNil(document.id)
        XCTAssertNotNil(document.createdAt)
        XCTAssertNotNil(document.modifiedAt)
    }
    
    func testDocumentWordCount() {
        let document = Document(text: "Hello world this is a test", title: "Test")
        XCTAssertEqual(document.wordCount, 6)
        
        let emptyDocument = Document(text: "", title: "Empty")
        XCTAssertEqual(emptyDocument.wordCount, 0)
        
        let singleWordDocument = Document(text: "Hello", title: "Single")
        XCTAssertEqual(singleWordDocument.wordCount, 1)
    }
    
    func testDocumentTextUpdate() {
        var document = Document(text: "Original text", title: "Test")
        let originalModifiedTime = document.modifiedAt
        
        // Small delay to ensure different timestamp
        Thread.sleep(forTimeInterval: 0.01)
        
        document.updateText("Updated text")
        
        XCTAssertEqual(document.text, "Updated text")
        XCTAssertGreaterThan(document.modifiedAt, originalModifiedTime)
    }
    
    func testMarkdownGenerator() {
        let generator = MarkdownGenerator()
        let input = "# Test Heading\n\nSome content with \\page marker"
        let output = generator.generateHomebreweryMarkdown(from: input)
        
        // Should pass through unchanged
        XCTAssertEqual(output, input)
    }
    
    func testMarkdownHeadingExtraction() {
        let generator = MarkdownGenerator()
        let markdown = """
        # Main Heading
        Some content here
        ## Subheading
        More content
        ### Another heading
        Final content
        """
        
        let headings = generator.extractHeadings(from: markdown)
        XCTAssertEqual(headings.count, 3)
        XCTAssertEqual(headings[0], "# Main Heading")
        XCTAssertEqual(headings[1], "## Subheading")
        XCTAssertEqual(headings[2], "### Another heading")
    }
    
    func testSecretsManagerValidation() {
        let secretsManager = SecretsManager.shared
        
        // Test invalid keys
        XCTAssertFalse(secretsManager.isValidKey(nil))
        XCTAssertFalse(secretsManager.isValidKey(""))
        XCTAssertFalse(secretsManager.isValidKey("YOUR_API_KEY"))
        XCTAssertFalse(secretsManager.isValidKey("YOUR_OPENAI_API_KEY"))
        
        // Test valid key
        XCTAssertTrue(secretsManager.isValidKey("sk-1234567890abcdef"))
    }
    
    func testLLMError() {
        let apiKeyError = LLMError.apiKeyMissing
        XCTAssertNotNil(apiKeyError.errorDescription)
        XCTAssertTrue(apiKeyError.errorDescription!.contains("API key"))
        
        let statusError = LLMError.unexpectedStatusCode(statusCode: 404, responseBody: "Not found")
        XCTAssertNotNil(statusError.errorDescription)
        XCTAssertTrue(statusError.errorDescription!.contains("404"))
        XCTAssertTrue(statusError.errorDescription!.contains("Not found"))
    }
    
    func testCampaignCreatorBasicFunctionality() {
        let creator = CampaignCreator()
        
        // Test document creation
        let document = creator.createDocument(title: "Test Campaign", text: "Test content")
        XCTAssertEqual(document.title, "Test Campaign")
        XCTAssertEqual(document.text, "Test content")
        
        // Test document listing
        let documents = creator.listDocuments()
        XCTAssertEqual(documents.count, 1)
        XCTAssertEqual(documents.first?.title, "Test Campaign")
        
        // Test Homebrewery export
        let exportedMarkdown = creator.exportToHomebrewery(document)
        XCTAssertEqual(exportedMarkdown, "Test content")
    }
}