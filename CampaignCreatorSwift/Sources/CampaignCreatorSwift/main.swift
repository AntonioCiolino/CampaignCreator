import Foundation
import CampaignCreatorLib

@main
struct CampaignCreatorApp {
    static func main() {
        print("🎲 Welcome to Campaign Crafter Swift!")
        print("======================================")
        
        let campaignCreator = CampaignCreator()
        campaignCreator.showStatus()
        
        // Demo functionality
        demonstrateFeatures(campaignCreator)
    }
    
    static func demonstrateFeatures(_ creator: CampaignCreator) {
        print("🚀 Demonstrating Campaign Crafter features...\n")
        
        // 1. Create a sample document
        let document = creator.createDocument(
            title: "My First Campaign",
            text: """
            # The Lost Kingdom of Aethermoor
            
            ## Overview
            A mystical realm where magic and technology coexist in delicate balance.
            
            ## Key Locations
            
            ### The Crystal Citadel
            A magnificent fortress built entirely from enchanted crystals.
            
            ### The Steamworks District
            Where inventors and artificers craft mechanical wonders.
            
            \\page
            
            ## Notable NPCs
            
            ### Archmage Thyrin
            *Medium humanoid (elf), neutral good*
            
            **Armor Class** 17 (Natural Armor)
            **Hit Points** 165 (22d10 + 44)
            **Speed** 30 ft., fly 60 ft.
            
            A powerful mage who guards the ancient secrets of Aethermoor.
            """
        )
        
        print("📄 Created document: '\(document.title)'")
        print("   Word count: \(document.wordCount)")
        print("   Character count: \(document.size)")
        
        // 2. Generate Homebrewery export
        let homebreweryMarkdown = creator.exportToHomebrewery(document)
        print("\n📋 Homebrewery export ready (first 200 chars):")
        print(String(homebreweryMarkdown.prefix(200)))
        if homebreweryMarkdown.count > 200 {
            print("...")
        }
        
        // 3. Try LLM generation if available
        if SecretsManager.shared.hasAnyAPIKey {
            print("\n🤖 Testing LLM text generation...")
            
            let semaphore = DispatchSemaphore(value: 0)
            
            creator.generateText(prompt: "Create a brief description of a magical tavern in a fantasy setting.") { result in
                switch result {
                case .success(let generatedText):
                    print("✅ Generated text:")
                    print(generatedText)
                case .failure(let error):
                    print("❌ Generation failed: \(error.localizedDescription)")
                }
                semaphore.signal()
            }
            
            semaphore.wait()
        } else {
            print("\n⚠️  No API keys configured. To test LLM features, set environment variables:")
            print("   export OPENAI_API_KEY='your-key-here'")
            print("   export GEMINI_API_KEY='your-key-here'")
        }
        
        // 4. Show final status
        creator.showStatus()
        
        print("✨ Demo complete! Campaign Crafter Swift is operational.")
    }
}
