import Foundation
import CampaignCreatorLib

@main
struct CampaignCreatorCLI { // Renamed struct to avoid conflict with iOS App struct name if linked
    static func main() {
        print("🎲 Welcome to Campaign Crafter Swift (CLI)!")
        print("==========================================")
        
        let campaignCreator = CampaignCreator()
        campaignCreator.showStatus()
        
        // Demo functionality
        demonstrateFeatures(campaignCreator)
    }
    
    static func demonstrateFeatures(_ creator: CampaignCreator) {
        print("🚀 Demonstrating Campaign Crafter features...\n")
        
        // 1. Create a sample campaign and add a section
        var campaign = creator.createCampaign(title: "My First Campaign")

        let initialContent = """
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

        let section1 = CampaignSection(title: "Chapter 1: Introduction to Aethermoor", content: initialContent, order: 0)
        campaign.sections.append(section1)
        campaign.markAsModified() // Ensure modifiedAt is updated
        creator.updateCampaign(campaign) // Save changes to CampaignCreator's list

        // Fetch the updated campaign from creator to ensure we have the instance managed by it
        guard let updatedCampaign = creator.listCampaigns().first(where: { $0.id == campaign.id }) else {
            print("Error: Could not retrieve updated campaign.")
            return
        }
        campaign = updatedCampaign // Work with the updated instance

        print("📄 Created campaign: '\(campaign.title)'")
        print("   Section count: \(campaign.sections.count)")
        if let firstSection = campaign.sections.first {
            print("   First section title: \(firstSection.title ?? "Untitled Section")")
        }
        print("   Total word count: \(campaign.wordCount)")
        
        // 2. Generate Homebrewery export
        let homebreweryMarkdown = creator.exportCampaignToHomebrewery(campaign)
        print("\n📋 Homebrewery export ready (first 200 chars):")
        print(String(homebreweryMarkdown.prefix(200)))
        if homebreweryMarkdown.count > 200 {
            print("...")
        }
        
        // 3. Try LLM generation if available
        if SecretsManager.shared.hasAnyAPIKey {
            print("\n🤖 Testing LLM text generation...")
            
            let semaphore = DispatchSemaphore(value: 0)
            
            // Generate text for the campaign's concept or a new section
            let promptForLLM = "Based on the campaign '\(campaign.title)', describe a mysterious artifact hidden within The Crystal Citadel."

            creator.generateText(prompt: promptForLLM) { result in
                switch result {
                case .success(let generatedText):
                    print("✅ Generated text for campaign artifact:")
                    print(generatedText)
                    // Optionally, add this as a new section or part of the concept
                    // For demo, we'll just print it.
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
        
        // 4. Demonstrate character creation
        print("\n👤 Demonstrating Character creation...")
        let char1 = creator.createCharacter(name: "Sir Reginald")
        var updatedChar1 = char1
        updatedChar1.description = "A noble knight."
        creator.updateCharacter(updatedChar1)

        let char2 = creator.createCharacter(name: "Misty Shadowfoot")
        var updatedChar2 = char2
        updatedChar2.description = "A cunning rogue."
        creator.updateCharacter(updatedChar2)

        // 5. Show final status
        creator.showStatus()
        
        print("✨ Demo complete! Campaign Crafter Swift (CLI) is operational.")
    }
}
