import SwiftUI
import Kingfisher
import SwiftData

struct CharacterDetailView: View {
    let character: CampaignCreatorLib.Character

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // your UI...
            }
            .padding()
        }
        .navigationTitle(character.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button("Edit") {
                    // ...
                }
            }
        }
    }
}
