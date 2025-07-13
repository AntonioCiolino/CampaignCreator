import SwiftUI

struct MemorySummaryView: View {
    let memorySummary: String
    @State private var isExpanded: Bool = false

    var body: some View {
        VStack(alignment: .leading) {
            HStack {
                Text("Memory Summary")
                    .font(.headline)
                Spacer()
                Button(action: {
                    withAnimation {
                        isExpanded.toggle()
                    }
                }) {
                    Image(systemName: isExpanded ? "chevron.up.circle.fill" : "chevron.down.circle.fill")
                        .font(.title2)
                }
            }
            .padding(.bottom, 4)

            if isExpanded {
                ScrollView {
                    Text(memorySummary)
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                        .frame(maxHeight: 200)
                }
                .transition(.asymmetric(insertion: .scale, removal: .opacity))
            }
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 10).fill(Color.white).shadow(radius: 2))
    }
}

struct MemorySummaryView_Previews: PreviewProvider {
    static var previews: some View {
        MemorySummaryView(memorySummary: "This is a longer summary of the character's memories, discussing their recent adventures, key decisions, and relationships formed. It might include details about their victory against the goblin horde, the tense negotiation with the merchant king, and the budding friendship with the enigmatic sorcerer they met in the cursed woods. The summary is designed to provide a quick yet comprehensive overview of the character's journey so far.")
            .padding()
    }
}
