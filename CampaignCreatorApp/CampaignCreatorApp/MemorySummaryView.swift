import SwiftUI

struct MemorySummaryView: View {
    let memorySummary: String
    @Environment(\.presentationMode) var presentationMode

    var body: some View {
        NavigationView {
            ScrollView {
                Text(memorySummary)
                    .padding()
            }
            .navigationTitle("Memory Summary")
            .navigationBarItems(trailing: Button("Done") {
                presentationMode.wrappedValue.dismiss()
            })
        }
    }
}

struct MemorySummaryView_Previews: PreviewProvider {
    static var previews: some View {
        MemorySummaryView(memorySummary: "This is a longer summary of the character's memories, discussing their recent adventures, key decisions, and relationships formed. It might include details about their victory against the goblin horde, the tense negotiation with the merchant king, and the budding friendship with the enigmatic sorcerer they met in the cursed woods. The summary is designed to provide a quick yet comprehensive overview of the character's journey so far.")
            .padding()
    }
}
