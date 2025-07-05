# CampaignCreator Swift

A modern, functional Swift implementation of the Campaign Creator application, built using Swift Package Manager.

## Overview

This is a complete rewrite of the original iOS TextEditorApp, now as a cross-platform Swift package that can run on macOS, Linux, and potentially other Swift-supported platforms. The application provides core campaign creation functionality including:

- **Document Management**: Create, edit, and manage campaign documents
- **Markdown Generation**: Export content in Homebrewery-compatible format
- **LLM Integration**: Generate text using OpenAI GPT models (when API keys are provided)
- **Extensible Architecture**: Designed to support additional LLM providers

## Features

✅ **Operational Swift Application** - Builds and runs successfully
✅ **Document Management** - Create and manage campaign documents with word count, timestamps
✅ **Markdown Export** - Generate Homebrewery-compatible markdown
✅ **LLM Integration** - OpenAI GPT integration (requires API key)
✅ **Comprehensive Testing** - Full test suite with 8 passing tests
✅ **Modern Swift** - Uses Swift 6.1 with concurrency support
✅ **Cross-Platform** - Runs on macOS, Linux, and other Swift platforms

## Quick Start

### Prerequisites

- Swift 6.1 or later
- Optional: OpenAI API key for LLM features

### Installation

```bash
# Clone the repository
git clone https://github.com/AntonioCiolino/CampaignCreator.git
cd CampaignCreator/CampaignCreatorSwift

# Build the project
swift build

# Run the application
swift run
```

### With LLM Features

To enable OpenAI text generation:

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
swift run
```

## Usage

The application runs a demonstration of all core features:

1. **Document Creation**: Creates a sample D&D campaign document
2. **Text Processing**: Counts words and characters
3. **Markdown Export**: Generates Homebrewery-compatible output
4. **LLM Generation**: If API keys are available, demonstrates text generation

### Example Output

```
🎲 Welcome to Campaign Creator Swift!
======================================
⚠️  OpenAI service not available: API key is missing. Please provide it via environment variable.

=== Campaign Creator Status ===
Available Services: 
Documents loaded: 0
================================

🚀 Demonstrating Campaign Creator features...

📄 Created document: 'My First Campaign'
   Word count: 84
   Character count: 553

📋 Homebrewery export ready (first 200 chars):
# The Lost Kingdom of Aethermoor

## Overview
A mystical realm where magic and technology coexist in delicate balance.
...

✨ Demo complete! Campaign Creator Swift is operational.
```

## Architecture

The project follows modern Swift best practices:

### Core Components

- **CampaignCreatorLib**: Main library containing all business logic
  - `Document`: Data model for campaign documents
  - `LLMService`: Protocol for language model integrations
  - `OpenAIClient`: OpenAI GPT implementation
  - `MarkdownGenerator`: Homebrewery export functionality
  - `SecretsManager`: Environment-based API key management
  - `CampaignCreator`: Main application controller

- **CampaignCreatorSwift**: Executable target with command-line interface

### Testing

Comprehensive test suite covering:
- Document creation and manipulation
- Markdown generation and processing
- API key validation
- Error handling
- Core application functionality

## Development

### Running Tests

```bash
swift test
```

### Building for Release

```bash
swift build -c release
```

### Adding New LLM Providers

1. Create a new client class implementing `LLMService`
2. Add configuration to `SecretsManager` 
3. Update `CampaignCreator` initialization logic
4. Add tests for the new provider

## API Keys and Security

- API keys are loaded from environment variables (never hardcoded)
- Supports OpenAI GPT models
- Extensible for additional providers (Gemini, Anthropic, etc.)
- No keys are stored in source code or committed to the repository

## Comparison to Legacy iOS App

| Feature | Legacy iOS App | Swift Package |
|---------|---------------|---------------|
| Platform | iOS only | Cross-platform |
| Build System | Xcode project | Swift Package Manager |
| Dependencies | Xcode/Swift Package Manager | Swift Package Manager |
| Testing | Limited | Comprehensive test suite |
| API Keys | Hardcoded Secrets.swift | Environment variables |
| Architecture | UIKit/Storyboards | Protocol-oriented design |
| Maintenance | Outdated/Legacy | Modern Swift 6.1 |

## Future Enhancements

- [ ] Additional LLM provider support (Gemini, Anthropic)
- [ ] File I/O operations for document persistence
- [ ] Interactive command-line interface
- [ ] Web service API
- [ ] iOS/macOS UI layer

## Contributing

1. Ensure Swift 6.1+ is installed
2. Run tests: `swift test`
3. Follow existing code style and patterns
4. Add tests for new functionality

## License

This project follows the same license as the main CampaignCreator repository.