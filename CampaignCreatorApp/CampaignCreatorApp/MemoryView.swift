import SwiftUI

struct MemoryView: View {
    @ObservedObject var viewModel: MemoryViewModel
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            VStack {
                ScrollView {
                    TextEditor(text: $viewModel.memory.summary)
                        .padding()
                }

                Spacer()

                Button(action: {
                    viewModel.forceSummarizeMemory()
                }) {
                    Text("Force Summary")
                }
                .buttonStyle(.bordered)

                Button(action: {
                    // viewModel.syncMemory()
                }) {
                    Text("Sync to Server")
                }
                .buttonStyle(.borderedProminent)
                .padding(.top, 10)
                .disabled(true)
            }
            .padding()
            .navigationTitle("Memory")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}
