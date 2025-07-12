//
//  CommonMoodboardView.swift
//  CampaignCreatorApp
//
//  Created by Jules on 2/20/24.
//

import SwiftUI
import CampaignCreatorLib
import Kingfisher

enum MoodboardAction {
    case addFromURL
    case generateWithAI
    case reorder
    case delete
}

struct CommonMoodboardView: View {
    @State var title: String
    @Binding var imageURLs: [String]

    var onSave: (([String]) -> Void)?
    var onGenerateAIImage: ((String) -> Task<String?, Error>)?

    @State private var showingAddImageOptions = false
    @State private var showingAddURLSheet = false
    @State private var showingGenerateImageSheet = false
    @State private var newImageURLInput: String = ""
    @State private var aiImagePromptInput: String = ""
    @State private var isGeneratingAIImage = false
    @State private var alertItem: AlertMessageItem?

    @State private var editMode: EditMode = .inactive

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]

    var body: some View {
        ScrollView {
            if imageURLs.isEmpty {
                Text("No images available.")
                    .font(.headline)
                    .foregroundColor(.secondary)
            } else {
                ImageGrid(imageURLs: $imageURLs, editMode: $editMode, onDelete: { indexSet in
                    imageURLs.remove(atOffsets: indexSet)
                })
            }
        }
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                if let onSave = onSave {
                    Button("Save") {
                        onSave(imageURLs)
                    }
                }
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack {
                    if onGenerateAIImage != nil {
                        Button(action: { showingAddImageOptions = true }) {
                            Image(systemName: "plus")
                        }
                    }

                    EditButton()
                }
            }
        }
        .environment(\.editMode, $editMode)
        .confirmationDialog("Add Image", isPresented: $showingAddImageOptions, titleVisibility: .visible) {
            Button("Add from URL") {
                newImageURLInput = ""
                showingAddURLSheet = true
            }
            if onGenerateAIImage != nil {
                Button("Generate with AI") {
                    aiImagePromptInput = ""
                    showingGenerateImageSheet = true
                }
            }
        }
        .sheet(isPresented: $showingAddURLSheet) {
            addImageView
        }
        .sheet(isPresented: $showingGenerateImageSheet) {
            generateImageView
        }
        .alert(item: $alertItem) { item in
            Alert(title: Text("Moodboard"), message: Text(item.message), dismissButton: .default(Text("OK")))
        }
    }

    private var addImageView: some View {
        NavigationView {
            Form {
                Section(header: Text("Image URL")) {
                    TextField("https://example.com/image.png", text: $newImageURLInput)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                }
                Button("Add Image") {
                    if let url = URL(string: newImageURLInput), UIApplication.shared.canOpenURL(url) {
                        imageURLs.append(newImageURLInput)
                        showingAddURLSheet = false
                    } else {
                        alertItem = AlertMessageItem(message: "Invalid URL provided.")
                    }
                }
                .disabled(newImageURLInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .navigationTitle("Add Image from URL")
            .navigationBarItems(leading: Button("Cancel") { showingAddURLSheet = false })
        }
    }

    private var generateImageView: some View {
        NavigationView {
            Form {
                Section(header: Text("AI Image Prompt")) {
                    TextEditor(text: $aiImagePromptInput)
                        .frame(height: 100)
                }
                Button(action: {
                    Task {
                        await generateAIImage()
                    }
                }) {
                    HStack {
                        if isGeneratingAIImage {
                            ProgressView()
                            Text("Generating...")
                        } else {
                            Image(systemName: "sparkles")
                            Text("Generate Image")
                        }
                    }
                }
                .disabled(aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isGeneratingAIImage)
            }
            .navigationTitle("Generate Image")
            .navigationBarItems(leading: Button("Cancel") { showingGenerateImageSheet = false })
        }
    }

    private func generateAIImage() async {
        guard let onGenerateAIImage = onGenerateAIImage else { return }

        isGeneratingAIImage = true
        let prompt = aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines)

        do {
            if let newImageURL = try await onGenerateAIImage(prompt).value {
                imageURLs.append(newImageURL)
                showingGenerateImageSheet = false
            } else {
                alertItem = AlertMessageItem(message: "AI image generation succeeded but returned no URL.")
            }
        } catch {
            alertItem = AlertMessageItem(message: "Failed to generate AI image: \(error.localizedDescription)")
        }

        isGeneratingAIImage = false
    }
}
