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
                    .refreshable { // <<<< ADDED
                        await campaignCreator.fetchCampaigns()
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
                // Keep the existing onAppear logic for scenarios like app returning from background
                // or if the view appears when session is already valid.
                print("CampaignListView: .onAppear. SessionValid: \(campaignCreator.isUserSessionValid), Auth: \(campaignCreator.isAuthenticated), Loading: \(campaignCreator.isLoadingCampaigns), InitialFetchAttempted: \(campaignCreator.initialCampaignFetchAttempted), Err: \(campaignCreator.campaignError != nil ? (campaignCreator.campaignError?.localizedDescription ?? "Unknown Error") : "None")")
                // Simplified onAppear: if session is valid and we haven't tried loading, load.
                // The onChange modifier will handle the case where session becomes valid after appearing.
                if campaignCreator.isUserSessionValid && !campaignCreator.isLoadingCampaigns && !campaignCreator.initialCampaignFetchAttempted {
                     print("CampaignListView: .onAppear - Conditions met (SESSION VALID, not loading, not attempted), will fetch campaigns.")
                     Task {
                         await campaignCreator.fetchCampaigns()
                     }
                } else if campaignCreator.isUserSessionValid && campaignCreator.campaignError != nil && !campaignCreator.isLoadingCampaigns {
                     print("CampaignListView: .onAppear - Conditions met (SESSION VALID, error present, not loading), will attempt retry fetch campaigns.")
                     Task {
                         await campaignCreator.fetchCampaigns() // Retry on error
                     }
                } else {
                     print("CampaignListView: .onAppear - Conditions not met for immediate fetch. isUserSessionValid: \(campaignCreator.isUserSessionValid), isLoading: \(campaignCreator.isLoadingCampaigns), initialAttempted: \(campaignCreator.initialCampaignFetchAttempted)")
                }
            }
            .onChange(of: campaignCreator.isUserSessionValid) { newSessionValidState in
                print("CampaignListView: .onChange(of: isUserSessionValid) triggered. New state: \(newSessionValidState)")
                if newSessionValidState && !campaignCreator.isLoadingCampaigns {
                    if !campaignCreator.initialCampaignFetchAttempted || campaignCreator.campaignError != nil {
                        print("CampaignListView: .onChange - Conditions met (SESSION NOW VALID, initial fetch needed or error retry), will fetch campaigns.")
                        Task {
                            await campaignCreator.fetchCampaigns()
                        }
                    } else {
                         print("CampaignListView: .onChange - Session valid, initial fetch already attempted and no error, skipping fetch. Campaigns count: \(campaignCreator.campaigns.count)")
                    }
                } else if !newSessionValidState {
                    print("CampaignListView: .onChange - Session became invalid. Campaigns will be cleared by logout logic if applicable.")
                    // If session becomes invalid, campaigns list is typically cleared by logout() in CampaignCreator
                } else {
                    print("CampaignListView: .onChange - Session valid but currently loading campaigns. Skipping fetch.")
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