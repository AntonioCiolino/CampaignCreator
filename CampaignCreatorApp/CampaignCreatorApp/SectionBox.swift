import SwiftUI

struct SectionBox<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) { // Added spacing
            Text(title).font(.headline)
            content
                .padding() // Added padding to content
                .frame(maxWidth: .infinity, alignment: .leading) // Added frame to content
                .background(Color(.systemGray6)) // Changed background color
                .cornerRadius(8) // This was already effectively here due to background being applied before main VStack's cornerRadius
        }
        .padding(.vertical, 8) // Changed padding of VStack
        // .background(Color(.secondarySystemBackground)) // Removed, as content now has its own background
        // .cornerRadius(8) // Removed, as content now has its own cornerRadius and background
        // If a separate outer background/cornerRadius is desired, it can be added back.
        // For now, assuming the content's background is sufficient.
    }
}

#Preview {
    SectionBox(title: "Sample Section") {
        Text("This is the content of the section.")
            .padding() // Match the new structure where content might need its own padding for preview
    }
    .padding() // Outer padding for the preview container
}
