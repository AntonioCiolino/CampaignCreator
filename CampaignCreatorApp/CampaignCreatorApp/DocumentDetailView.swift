import SwiftUI
import CampaignCreatorLib

struct DocumentDetailView: View {
    let document: Document
    let campaignCreator: CampaignCreator
    @State private var editedText: String
    @State private var isEditing = false
    @State private var showingGenerateSheet = false
    @State private var generatePrompt = ""
    @State private var isGenerating = false
    @State private var generationError: String?
    @State private var showingExportSheet = false
    @State private var exportedMarkdown = ""
    
    init(document: Document, campaignCreator: CampaignCreator) {
        self.document = document
        self.campaignCreator = campaignCreator
        self._editedText = State(initialValue: document.text)
    }
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Document info header
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("\(document.wordCount) words")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text("Modified: \(document.modifiedAt, style: .date)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        // Action buttons
                        HStack(spacing: 12) {
                            Button(action: {
                                showingGenerateSheet = true
                            }) {
                                Label("Generate", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderedProminent)
                            
                            Button(action: {
                                exportToHomebrewery()
                            }) {
                                Label("Export", systemImage: "square.and.arrow.up")
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                }
                .padding()
                .background(Color(.systemGroupedBackground))
                .cornerRadius(12)
                
                // Content editor
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Content")
                            .font(.headline)
                        
                        Spacer()
                        
                        Button(isEditing ? "Done" : "Edit") {
                            if isEditing {
                                // Save changes (in a real app, you'd update the document)
                                isEditing = false
                            } else {
                                isEditing = true
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                    
                    if isEditing {
                        TextEditor(text: $editedText)
                            .frame(minHeight: 300)
                            .padding(8)
                            .background(Color(.systemBackground))
                            .cornerRadius(8)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color(.systemGray4), lineWidth: 1)
                            )
                    } else {
                        Text(editedText.isEmpty ? "Tap Edit to add content..." : editedText)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .frame(minHeight: 200)
                            .padding()
                            .background(Color(.systemGroupedBackground))
                            .cornerRadius(8)
                            .foregroundColor(editedText.isEmpty ? .secondary : .primary)
                    }
                }
                .padding()
                .background(Color(.systemBackground))
                .cornerRadius(12)
            }
            .padding()
        }
        .navigationTitle(document.title)
        .navigationBarTitleDisplayMode(.large)
        .sheet(isPresented: $showingGenerateSheet) {
            NavigationView {
                VStack(spacing: 20) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("AI Text Generation")
                            .font(.headline)
                        
                        Text("Describe what you'd like to generate for this campaign document:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    TextEditor(text: $generatePrompt)
                        .frame(height: 120)
                        .padding(8)
                        .background(Color(.systemGroupedBackground))
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color(.systemGray4), lineWidth: 1)
                        )
                    
                    if let error = generationError {
                        Text(error)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                    
                    Spacer()
                    
                    Button(action: generateContent) {
                        HStack {
                            if isGenerating {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            }
                            Text(isGenerating ? "Generating..." : "Generate Content")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(generatePrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isGenerating)
                }
                .padding()
                .navigationTitle("Generate Content")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("Cancel") {
                            showingGenerateSheet = false
                            generatePrompt = ""
                            generationError = nil
                        }
                    }
                }
            }
            .presentationDetents([.medium, .large])
        }
        .sheet(isPresented: $showingExportSheet) {
            NavigationView {
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("Homebrewery Export")
                            .font(.headline)
                        
                        Text("Your document has been converted to Homebrewery-compatible markdown:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        Text(exportedMarkdown)
                            .font(.system(.body, design: .monospaced))
                            .padding()
                            .background(Color(.systemGroupedBackground))
                            .cornerRadius(8)
                        
                        Button("Copy to Clipboard") {
                            UIPasteboard.general.string = exportedMarkdown
                        }
                        .buttonStyle(.borderedProminent)
                        .frame(maxWidth: .infinity)
                    }
                    .padding()
                }
                .navigationTitle("Export")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Done") {
                            showingExportSheet = false
                        }
                    }
                }
            }
        }
    }
    
    private func generateContent() {
        guard !generatePrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        isGenerating = true
        generationError = nil
        
        campaignCreator.generateText(prompt: generatePrompt) { result in
            DispatchQueue.main.async {
                isGenerating = false
                
                switch result {
                case .success(let generatedText):
                    if editedText.isEmpty {
                        editedText = generatedText
                    } else {
                        editedText += "\n\n" + generatedText
                    }
                    showingGenerateSheet = false
                    generatePrompt = ""
                    isEditing = true // Automatically enter edit mode to show the new content
                    
                case .failure(let error):
                    generationError = error.localizedDescription
                }
            }
        }
    }
    
    private func exportToHomebrewery() {
        exportedMarkdown = campaignCreator.exportToHomebrewery(document)
        showingExportSheet = true
    }
}

#Preview {
    let campaignCreator = CampaignCreator()
    let sampleDocument = campaignCreator.createDocument(
        title: "Sample Campaign",
        text: "This is a sample campaign document with some content to display in the preview."
    )
    
    return NavigationView {
        DocumentDetailView(document: sampleDocument, campaignCreator: campaignCreator)
    }
}