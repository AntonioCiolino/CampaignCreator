import SwiftUI

struct TOCView: View {
    let sections: [CampaignSection]
    @Binding var selectedSection: CampaignSection?

    var body: some View {
        List(sections) { section in
            Button(action: {
                selectedSection = section
            }) {
                Text(section.title ?? "Untitled Section")
            }
        }
    }
}
