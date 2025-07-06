# Campaign Creator iOS App

A native iOS application for creating and managing tabletop RPG campaigns with AI assistance.

## Features

- **Document Management**: Create, edit, and organize campaign documents
- **AI Text Generation**: Generate campaign content using OpenAI GPT integration
- **Homebrewery Export**: Export documents in Homebrewery-compatible markdown format
- **Native iOS Interface**: SwiftUI-based interface optimized for iPhone and iPad

## Requirements

- iOS 15.0 or later
- Xcode 15.0 or later for development

## Installation

1. Open `CampaignCreatorApp.xcodeproj` in Xcode
2. Select your target device or simulator
3. Build and run the project

## Configuration

### API Keys

To use AI text generation features:

1. Open the app and go to the Settings tab
2. Add your OpenAI API key
3. The key will be securely stored on your device

## Architecture

The app is built using:

- **SwiftUI**: Modern iOS UI framework
- **CampaignCreatorLib**: Core functionality from the Swift Package Manager project
- **Combine**: Reactive programming for data binding

## Project Structure

```
CampaignCreatorApp/
├── CampaignCreatorApp.swift    # App entry point
├── ContentView.swift           # Main tab view
├── DocumentListView.swift      # Document list and creation
├── DocumentDetailView.swift    # Document editing and AI features
├── SettingsView.swift          # API key configuration
└── Assets.xcassets/           # App icons and colors
```

## Related Projects

This iOS app is part of the larger CampaignCreator project:

- `CampaignCreatorSwift/` - Swift Package with core functionality
- `campaign_crafter_ui/` - React web interface
- `campaign_crafter_api/` - FastAPI backend

## License

Same license as the main CampaignCreator repository.