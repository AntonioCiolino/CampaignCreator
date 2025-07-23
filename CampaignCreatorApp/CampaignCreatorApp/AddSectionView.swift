import SwiftUI

struct AddSectionView: View {
    @Binding var isPresented: Bool
    @State private var title = ""
    @State private var generateContent = false
    var onAdd: (String, Bool) -> Void

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Section Details")) {
                    TextField("Title", text: $title)
                    Toggle("Generate Content", isOn: $generateContent)
                }
            }
            .navigationTitle("Add Section")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        isPresented = false
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Add") {
                        onAdd(title, generateContent)
                        isPresented = false
                    }
                    .disabled(title.isEmpty)
                }
            }
        }
    }
}
