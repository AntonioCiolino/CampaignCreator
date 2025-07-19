import SwiftUI

struct MemorySummaryView: View {
    let memorySummary: String
    @State private var isExpanded: Bool = false

    var body: some View {
        DisclosureGroup("Memory Summary", isExpanded: $isExpanded) {
            Text(memorySummary)
                .font(.body)
                .padding(.top, 4)
        }
        .padding()
        .background(Color.gray.opacity(0.2))
        .cornerRadius(8)
    }
}
