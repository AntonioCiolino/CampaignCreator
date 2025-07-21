import SwiftUI
import CampaignCreatorLib

struct TOCView: View {
    @Bindable var campaign: CampaignModel
    @Binding var selectedSection: CampaignSection?
    let llmService: LLMService

    @State private var sseManager: SSEManager?
    @State private var isGeneratingTOC = false
    @State private var isSeedingSections = false
    @State private var tocError: String?
    @State private var seedError: String?
    @State private var autoPopulateSections = false

    var body: some View {
        VStack(alignment: .leading) {
            Text("Table of Contents")
                .font(.headline)

            if let toc = campaign.display_toc, !toc.isEmpty {
                ForEach(toc) { entry in
                    Text(entry.title ?? "Untitled Entry")
                }
            } else {
                Text("No Table of Contents generated yet.")
                    .foregroundColor(.secondary)
            }

            HStack {
                Button(action: {
                    generateTOC()
                }) {
                    Text("Generate TOC")
                }
                .disabled(isGeneratingTOC || isSeedingSections)

                if isGeneratingTOC {
                    ProgressView()
                }
            }

            if let tocError = tocError {
                Text(tocError)
                    .foregroundColor(.red)
            }

            if campaign.display_toc != nil && !campaign.display_toc!.isEmpty {
                HStack {
                    Button(action: {
                        seedSections()
                    }) {
                        Text("Seed Sections")
                    }
                    .disabled(isGeneratingTOC || isSeedingSections)

                    Toggle("Auto-populate sections", isOn: $autoPopulateSections)
                        .disabled(isGeneratingTOC || isSeedingSections)

                    if isSeedingSections {
                        ProgressView()
                    }
                }

                if let seedError = seedError {
                    Text(seedError)
                        .foregroundColor(.red)
                }
            }
        }
    }

    private func generateTOC() {
        isGeneratingTOC = true
        tocError = nil
        Task {
            do {
                let prompt = "Generate a table of contents for a campaign with the following concept: \(campaign.concept ?? "No concept provided"). The table of contents should be a list of sections that would be appropriate for a role-playing game campaign. Each section should have a title and a brief description."
                let updatedCampaign = try await llmService.apiService.generateCampaignTOC(campaignId: campaign.id, payload: LLMGenerationPayload(prompt: prompt))
                DispatchQueue.main.async {
                    self.campaign.display_toc = updatedCampaign.displayTOC?.map { TOCEntry(from: $0) }
                    self.isGeneratingTOC = false
                }
            } catch {
                DispatchQueue.main.async {
                    self.tocError = "Failed to generate TOC: \(error.localizedDescription)"
                    self.isGeneratingTOC = false
                }
            }
        }
    }

    private func seedSections() {
        isSeedingSections = true
        seedError = nil

        let sseManager = SSEManager()
        self.sseManager = sseManager

        sseManager.onOpen = {
            print("SSE connection opened")
        }

        sseManager.onMessage = { message in
            // Parse the SSE message and update the UI
            // For now, just print the message
            print("SSE message: \(message)")

            // Example of parsing the message and updating the campaign
            if let data = message.data(using: .utf8) {
                let decoder = JSONDecoder()
                if let seedEvent = try? decoder.decode(SeedSectionsEvent.self, from: data) {
                    if seedEvent.event_type == "section_update", let sectionData = seedEvent.section_data {
                        DispatchQueue.main.async {
                            self.campaign.sections?.append(sectionData)
                        }
                    }
                }
            }
        }

        sseManager.onError = { error in
            DispatchQueue.main.async {
                self.seedError = "Failed to seed sections: \(error.localizedDescription)"
                self.isSeedingSections = false
            }
        }

        sseManager.onComplete = {
            DispatchQueue.main.async {
                self.isSeedingSections = false
            }
        }

        guard let url = llmService.apiService.seedSectionsFromTocURL(campaignId: campaign.id, autoPopulate: autoPopulateSections) else {
            seedError = "Failed to create seed sections URL"
            isSeedingSections = false
            return
        }

        sseManager.connect(to: url)
    }
}
