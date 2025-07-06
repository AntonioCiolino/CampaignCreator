import SwiftUI
import CampaignCreatorLib

struct CampaignListView: View {
    // CampaignCreator is now an @MainActor class and uses @Published for campaigns
    @ObservedObject var campaignCreator: CampaignCreator
    @State private var showingCreateSheet = false
    @State private var newCampaignTitle = ""
    @State private var showCreationErrorAlert = false
    @State private var creationErrorMessage = ""

    var body: some View {
        NavigationView {
            Group { // Use Group to conditionally show content
                if campaignCreator.isLoadingCampaigns && campaignCreator.campaigns.isEmpty {
                    ProgressView("Loading Campaigns...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error = campaignCreator.campaignError {
                    VStack {
                        Text("Error Loading Campaigns")
                            .font(.headline)
                        Text(error.localizedDescription)
                            .font(.caption)
                            .multilineTextAlignment(.center)
                        Button("Retry") {
                            Task {
                                await campaignCreator.fetchCampaigns()
                            }
                        }
                        .padding(.top)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if campaignCreator.campaigns.isEmpty {
                    Text("No campaigns yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(campaignCreator.campaigns) { campaign in
                            NavigationLink(destination: CampaignDetailView(campaign: campaign, campaignCreator: campaignCreator)) {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(campaign.title)
                                        .font(.headline)
                                        .foregroundColor(.primary)
                                    HStack {
                                        Text("\(campaign.wordCount) words")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Spacer()
                                        Text("Sections: \(campaign.sections.count)")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Spacer()
                                        Text(campaign.modifiedAt != nil ? "\(campaign.modifiedAt!, style: .date)" : "N/A")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding(.vertical, 2)
                            }
                        }
                        .onDelete(perform: deleteCampaigns)
                    }
                }
            }
            .navigationTitle("Campaigns")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if campaignCreator.isLoadingCampaigns && !campaignCreator.campaigns.isEmpty {
                        ProgressView() // Show a small spinner if loading in background
                    }
                }
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
                        Section("Campaign Details") {
                            TextField("Campaign Title", text: $newCampaignTitle)
                        }
                    }
                    .navigationTitle("New Campaign")
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
                                Task {
                                    await createCampaign()
                                }
                            }
                            .disabled(newCampaignTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        }
                    }
                }
                .presentationDetents([.medium])
            }
            .alert("Error Creating Campaign", isPresented: $showCreationErrorAlert) {
                Button("OK") { }
            } message: {
                Text(creationErrorMessage)
            }
            .onAppear {
                print("CampaignListView: .onAppear. SessionValid: \(campaignCreator.isUserSessionValid), Auth: \(campaignCreator.isAuthenticated), Loading: \(campaignCreator.isLoadingCampaigns), InitialFetchAttempted: \(campaignCreator.initialCampaignFetchAttempted), Err: \(campaignCreator.campaignError != nil ? (campaignCreator.campaignError?.localizedDescription ?? "Unknown Error") : "None")")
                if campaignCreator.isUserSessionValid && !campaignCreator.isLoadingCampaigns {
                    if !campaignCreator.initialCampaignFetchAttempted || campaignCreator.campaignError != nil {
                        print("CampaignListView: Conditions met (SESSION VALID, initial fetch needed or error retry), will fetch campaigns.")
                        Task {
                            await campaignCreator.fetchCampaigns()
                        }
                    } else {
                        print("CampaignListView: Session valid, initial fetch already attempted and no error, skipping fetch. Campaigns count: \(campaignCreator.campaigns.count)")
                    }
                } else {
                    print("CampaignListView: Skipping fetch. SessionValid: \(campaignCreator.isUserSessionValid), Auth: \(campaignCreator.isAuthenticated), Loading: \(campaignCreator.isLoadingCampaigns)")
                }
            }
        }
    }

    private func createCampaign() async {
        let title = newCampaignTitle.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !title.isEmpty else { return }

        do {
            _ = try await campaignCreator.createCampaign(title: title)
            // CampaignCreator.fetchCampaigns() is called internally by createCampaign,
            // so the @Published campaigns array will update.
            showingCreateSheet = false
            newCampaignTitle = ""
        } catch let error as APIError {
            creationErrorMessage = error.localizedDescription
            showCreationErrorAlert = true
            print("❌ Error creating campaign: \(error.localizedDescription)")
        } catch {
            creationErrorMessage = "An unexpected error occurred: \(error.localizedDescription)"
            showCreationErrorAlert = true
            print("❌ Unexpected error creating campaign: \(error.localizedDescription)")
        }
    }

    private func deleteCampaigns(offsets: IndexSet) {
        let campaignsToDelete = offsets.map { campaignCreator.campaigns[$0] }
        Task {
            for campaign in campaignsToDelete {
                do {
                    try await campaignCreator.deleteCampaign(campaign)
                } catch {
                    // Handle error, e.g., show an alert to the user
                    print("Error deleting campaign \(campaign.title): \(error.localizedDescription)")
                    // Optionally, present an alert for the failed deletion
                }
            }
            // campaignCreator.fetchCampaigns() is called internally by deleteCampaign
        }
    }
}

#Preview {
    let previewCreator = CampaignCreator()
    // Optionally populate with some mock data for preview if API is not live
    // For async, previewing loading/error states might require more setup
    return CampaignListView(campaignCreator: previewCreator)
}