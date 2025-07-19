import SwiftUI

struct CampaignSectionView: View {
    let section: CampaignSection

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let title = section.title {
                Text(title)
                    .font(.title)
                    .fontWeight(.bold)
            }
            Text(section.content)
                .font(.body)
        }
        .padding()
    }
}
