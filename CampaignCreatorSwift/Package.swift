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
    ],
    targets: [
        .executableTarget(
            name: "CampaignCreatorSwift",
            dependencies: ["CampaignCreatorLib"]
            // No specific path needed here, defaults to "Sources/CampaignCreatorSwift" or "Sources" then "CampaignCreatorSwift"
        ),
        .target(
            name: "CampaignCreatorLib",
            dependencies: [],
            // path: "Sources/CampaignCreatorLib", // Path is relative to the package root
            // By default, SPM looks for sources in Sources/<TargetName>.
            // If files are directly in Sources/CampaignCreatorLib and Sources/CampaignCreatorLib/Models,
            // it should find them.
            // Let's explicitly list them to be sure, especially since Document.swift was removed.
            sources: [
                "CampaignCreator.swift",
                "LLMService.swift",
                "MarkdownGenerator.swift",
                "OpenAIClient.swift",
                "OpenAIDataStructures.swift",
                "SecretsManager.swift",
                "Models/CampaignModel.swift",
                "Models/CharacterModel.swift"
            ]
            // Ensure the path to these sources is relative to "Sources/CampaignCreatorLib/"
            // If `sources` are specified, the `path` parameter defines where these `sources` strings are relative to.
            // If `path` is "Sources/CampaignCreatorLib", then the paths in `sources` are correct.
            // If `path` is omitted, it defaults to "Sources/<target_name>", which is "Sources/CampaignCreatorLib".
        ),
        .testTarget(
            name: "CampaignCreatorLibTests",
            dependencies: ["CampaignCreatorLib"]
            // path: "Tests/CampaignCreatorLibTests" // Default path
        ),
    ]
)
