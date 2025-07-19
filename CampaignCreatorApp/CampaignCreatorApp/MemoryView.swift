import SwiftUI

struct MemoryView: View {
    @ObservedObject var viewModel: MemoryViewModel
    @Environment(\.dismiss) var dismiss
    @State private var isForcingSummary = false
    @State private var showingSuccessAlert = false

    var body: some View {
        NavigationView {
            VStack {
                ScrollView {
                    TextEditor(text: $viewModel.memory.summary)
                        .padding()
                }

                Spacer()

                Button(action: {
                    isForcingSummary = true
                    viewModel.forceSummarizeMemory {
                        isForcingSummary = false
                        showingSuccessAlert = true
                    }
                }) {
                    if isForcingSummary {
                        ProgressView()
                    } else {
                        Text("Force Summary")
                    }
                }
                .buttonStyle(.bordered)
                .disabled(isForcingSummary)
                .alert("Success", isPresented: $showingSuccessAlert) {
                    Button("OK", role: .cancel) { }
                } message: {
                    Text("Memory summary updated successfully.")
                }

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
