import SwiftUI
import CampaignCreatorLib

struct DocumentListView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @State private var documents: [Document] = []
    @State private var showingCreateSheet = false
    @State private var newDocumentTitle = ""
    @State private var selectedDocument: Document?
    
    var body: some View {
        NavigationView {
            List {
                ForEach(documents, id: \.id) { document in
                    NavigationLink(destination: DocumentDetailView(document: document, campaignCreator: campaignCreator)) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(document.title)
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            HStack {
                                Text("\(document.wordCount) words")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                
                                Spacer()
                                
                                Text(document.modifiedAt, style: .date)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.vertical, 2)
                    }
                }
                .onDelete(perform: deleteDocuments)
            }
            .navigationTitle("Campaign Documents")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet) {
                NavigationView {
                    Form {
                        Section("Document Details") {
                            TextField("Document Title", text: $newDocumentTitle)
                        }
                    }
                    .navigationTitle("New Document")
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Cancel") {
                                showingCreateSheet = false
                                newDocumentTitle = ""
                            }
                        }
                        
                        ToolbarItem(placement: .navigationBarTrailing) {
                            Button("Create") {
                                createDocument()
                            }
                            .disabled(newDocumentTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        }
                    }
                }
                .presentationDetents([.medium])
            }
            .onAppear {
                loadDocuments()
            }
            
            // Detail view placeholder
            Text("Select a document to view details")
                .foregroundColor(.secondary)
                .font(.title2)
        }
    }
    
    private func loadDocuments() {
        documents = campaignCreator.listDocuments()
    }
    
    private func createDocument() {
        let title = newDocumentTitle.trimmingCharacters(in: .whitespacesAndNewlines)
        let document = campaignCreator.createDocument(title: title)
        documents = campaignCreator.listDocuments()
        
        showingCreateSheet = false
        newDocumentTitle = ""
    }
    
    private func deleteDocuments(offsets: IndexSet) {
        // For now, we'll just remove from the local array
        // In a full implementation, we'd remove from the campaignCreator as well
        documents.remove(atOffsets: offsets)
    }
}

#Preview {
    DocumentListView(campaignCreator: CampaignCreator())
}