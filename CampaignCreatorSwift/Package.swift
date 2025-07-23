// swift-tools-version:5.5
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
        .package(url: "https://github.com/onevcat/Kingfisher.git", from: "7.0.0")
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
            path: "Sources/CampaignCreatorLib",
            sources: [
                "CampaignCreator.swift",
                "APIService.swift",
                "LLMService.swift",
                "MarkdownGenerator.swift",
                "OpenAIClient.swift",
                "OpenAIDataStructures.swift",
                "SecretsManager.swift",
                "KeychainHelper.swift",
                "Models/CampaignModel.swift",
                "Models/CharacterModel.swift",
                "Models/UserModel.swift",
                "Models/FeatureModel.swift",
                "Models/ImageGenerationModels.swift",
                "Models/SectionRegeneratePayload.swift",
                "Models/ChatMessageData.swift",
                "Models/APIChatMessageModels.swift",
                "Models/Token.swift",
                "JSONDecoder+Extensions.swift",
                "TokenManager.swift",
                "Notifications.swift"
            ]
        ),
        .testTarget(
            name: "CampaignCreatorLibTests",
            dependencies: ["CampaignCreatorLib"]
        ),
    ]
)
