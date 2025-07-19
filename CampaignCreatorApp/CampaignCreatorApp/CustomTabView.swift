import SwiftUI

struct CustomTabView<Content: View>: View {
    let content: Content
    @Binding var selection: Int

    init(selection: Binding<Int>, @ViewBuilder content: () -> Content) {
        self._selection = selection
        self.content = content()
    }

    var body: some View {
        VStack(spacing: 0) {
            content
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            HStack {
                // This is a simplified implementation. In a real app, you would want to
                // create a more robust way to handle the tabs.
                Button(action: { selection = 0 }) {
                    VStack {
                        Image(systemName: "doc.text.fill")
                        Text("Campaigns")
                    }
                }
                .foregroundColor(selection == 0 ? .blue : .gray)

                Spacer()

                Button(action: { selection = 1 }) {
                    VStack {
                        Image(systemName: "person.3.fill")
                        Text("Characters")
                    }
                }
                .foregroundColor(selection == 1 ? .blue : .gray)

                Spacer()

                Button(action: { selection = 2 }) {
                    VStack {
                        Image(systemName: "gear")
                        Text("Settings")
                    }
                }
                .foregroundColor(selection == 2 ? .blue : .gray)
            }
            .padding(.horizontal)
            .padding(.top, 8)
        }
    }
}
