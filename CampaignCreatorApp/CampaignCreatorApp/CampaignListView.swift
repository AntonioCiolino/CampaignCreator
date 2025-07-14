import SwiftUI
import Kingfisher
import SwiftData

struct CampaignListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Campaign.title) private var campaigns: [Campaign]
    @State private var showingCreateSheet = false

    var body: some View {
        NavigationView {
            Group {
                if campaigns.isEmpty {
                    Text("No campaigns yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(campaigns) { campaign in
                            NavigationLink(destination: CampaignDetailView(campaign: campaign)) {
                                HStack {
                                    if let badgeURL = campaign.badge_image_url, let url = URL(string: badgeURL) {
                                        KFImage(url)
                                            .resizable()
                                            .aspectRatio(contentMode: .fill)
                                            .frame(width: 40, height: 40)
                                            .clipped()
                                            .cornerRadius(4)
                                    } else {
                                        Image(systemName: "photo")
                                            .resizable()
                                            .aspectRatio(contentMode: .fit)
                                            .frame(width: 40, height: 40)
                                            .foregroundColor(.gray)
                                    }
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(campaign.title)
                                            .font(.headline)
                                            .foregroundColor(.primary)
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
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet) {
                CampaignCreateView(isPresented: $showingCreateSheet)
            }
        }
    }

    private func deleteCampaigns(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                modelContext.delete(campaigns[index])
            }
        }
    }
}
