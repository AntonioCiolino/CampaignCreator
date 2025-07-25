// swift-tools-version: 6.1
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "CampaignCreatorSwift",
    platforms: [
        .macOS(.v10_15),
        .iOS(.v13),
        .tvOS(.v13),
        .watchOS(.v6)
    ],
    products: [
        .executable(name: "CampaignCreatorSwift", targets: ["CampaignCreatorSwift"]),
        .library(name: "CampaignCreatorLib", targets: ["CampaignCreatorLib"])
    ],
    dependencies: [
        // Add dependencies here as needed
        .package(url: "https://github.com/onevcat/Kingfisher.git", from: "8.0.0")
    ],
    targets: [
        .executableTarget(
            name: "CampaignCreatorSwift",
            dependencies: ["CampaignCreatorLib"]
        ),
        .target(
            name: "CampaignCreatorLib",
            dependencies: [
                .product(name: "Kingfisher", package: "Kingfisher")
            ],
            sources: [
                "CampaignCreator.swift",
                "APIService.swift", // Ensure APIService is here
                "LLMService.swift",
                "MarkdownGenerator.swift",
                "OpenAIClient.swift",
                "OpenAIDataStructures.swift",
                "SecretsManager.swift",
                "KeychainHelper.swift",
                "Models/CampaignModel.swift",
                "Models/CharacterModel.swift",
                "Models/UserModel.swift", // Added UserModel.swift
                "Models/FeatureModel.swift", // ADDED
                "Models/ImageGenerationModels.swift", // ADDED
                "Models/SectionRegeneratePayload.swift", // ADDED
                "Models/ChatMessageData.swift",
                "Models/APIChatMessageModels.swift", // Added new chat message models
                "Models/Token.swift",
                "JSONDecoder+Extensions.swift",
                "TokenManager.swift"
            ]
        ),
        .testTarget(
            name: "CampaignCreatorLibTests",
            dependencies: ["CampaignCreatorLib"]
        ),
    ]
)
