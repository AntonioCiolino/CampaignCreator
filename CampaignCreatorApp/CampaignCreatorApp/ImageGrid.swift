//
//  ImageGrid.swift
//  CampaignCreatorApp
//
//  Created by Jules on 2/20/24.
//

import SwiftUI
import Kingfisher

struct ImageGrid: View {
    @Binding var imageURLs: [String]
    @Binding var editMode: EditMode

    var onDelete: ((IndexSet) -> Void)?

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]

    var body: some View {
        LazyVGrid(columns: gridItemLayout, spacing: 2) {
            ForEach(imageURLs.indices, id: \.self) { index in
                ZStack(alignment: .topTrailing) {
                    KFImage(URL(string: imageURLs[index]))
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(minWidth: 0, maxWidth: .infinity, minHeight: 120, maxHeight: 120)
                        .clipped()

                    if editMode.isEditing {
                        Button(action: {
                            onDelete?(IndexSet(integer: index))
                        }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.red)
                                .background(Color.white.clipShape(Circle()))
                                .padding(4)
                        }
                    }
                }
            }
            .onMove(perform: move)
        }
        .padding(2)
    }

    private func move(from source: IndexSet, to destination: Int) {
        imageURLs.move(fromOffsets: source, toOffset: destination)
    }
}
