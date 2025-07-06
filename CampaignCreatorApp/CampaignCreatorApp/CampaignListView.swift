import SwiftUI
import CampaignCreatorLib

struct CampaignListView: View {
    @ObservedObject var campaignCreator: CampaignCreator // Keep as ObservedObject if CampaignCreator is an ObservableObject
    @State private var campaigns: [Campaign] = []
    @State private var showingCreateSheet = false
    @State private var newCampaignTitle = ""
    // selectedCampaign might be needed if you want to show a master-detail view on iPadOS/macOS
    // @State private var selectedCampaign: Campaign?

    var body: some View {
        NavigationView {
            List {
                ForEach(campaigns) { campaign in // Campaign is Identifiable
                    NavigationLink(destination: CampaignDetailView(campaign: campaign, campaignCreator: campaignCreator)) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(campaign.title)
                                .font(.headline)
                                .foregroundColor(.primary)

                            HStack {
                                // Display word count from campaign.wordCount (sum of sections)
                                Text("\(campaign.wordCount) words")
                                    .font(.caption)
                                    .foregroundColor(.secondary)

                                Spacer()

                                Text("Sections: \(campaign.sections.count)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)

                                Spacer()

                                Text(campaign.modifiedAt, style: .date)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.vertical, 2)
                    }
                }
                .onDelete(perform: deleteCampaigns)
            }
            .navigationTitle("Campaigns") // Updated title
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet) {
                NavigationView {
                    Form {
                        Section("Campaign Details") { // Updated section title
                            TextField("Campaign Title", text: $newCampaignTitle)
                        }
                    }
                    .navigationTitle("New Campaign") // Updated navigation title
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Cancel") {
                                showingCreateSheet = false
                                newCampaignTitle = ""
                            }
                        }

                        ToolbarItem(placement: .navigationBarTrailing) {
                            Button("Create") {
                                createCampaign()
                            }
                            .disabled(newCampaignTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        }
                    }
                }
                .presentationDetents([.medium])
            }
            .onAppear {
                loadCampaigns()
            }

            // Detail view placeholder for when no campaign is selected (especially for iPad/macOS)
            Text("Select a campaign to view details, or tap '+' to create a new one.")
                .foregroundColor(.secondary)
                .font(.title2)
        }
    }

    private func loadCampaigns() {
        campaigns = campaignCreator.listCampaigns()
    }

    private func createCampaign() {
        let title = newCampaignTitle.trimmingCharacters(in: .whitespacesAndNewlines)
        if !title.isEmpty {
            _ = campaignCreator.createCampaign(title: title) // CampaignCreator handles adding to its list
            loadCampaigns() // Reload to get the updated list including the new campaign
        }

        showingCreateSheet = false
        newCampaignTitle = ""
    }

    private func deleteCampaigns(offsets: IndexSet) {
        let campaignsToDelete = offsets.map { campaigns[$0] }
        for campaign in campaignsToDelete {
            campaignCreator.deleteCampaign(campaign)
        }
        loadCampaigns() // Reload to reflect deletions
    }
}

#Preview {
    CampaignListView(campaignCreator: CampaignCreator())
}