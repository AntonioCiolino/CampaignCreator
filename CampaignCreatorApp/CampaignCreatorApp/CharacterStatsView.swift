import SwiftUI

struct CharacterStatsView: View {
    let character: CharacterModel

    var body: some View {
        HStack {
            StatView(name: "STR", value: character.strength)
            StatView(name: "DEX", value: character.dexterity)
            StatView(name: "CON", value: character.constitution)
            StatView(name: "INT", value: character.intelligence)
            StatView(name: "WIS", value: character.wisdom)
            StatView(name: "CHA", value: character.charisma)
        }
        .padding()
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(8)
    }
}

struct StatView: View {
    let name: String
    let value: Int?

    var body: some View {
        VStack {
            Text(name)
                .font(.caption)
                .foregroundColor(.secondary)
            Text("\\(value ?? 0)")
                .font(.headline)
        }
        .frame(maxWidth: .infinity)
    }
}
