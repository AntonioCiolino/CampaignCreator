import React from 'react';
import LoadingSpinner from '../common/LoadingSpinner';
// import './CharacterChatPanel.css'; // CSS will be created in the next step

export interface CharacterChatPanelProps {
    characterName: string;
    isOpen: boolean;
    onClose: () => void;
    llmUserPrompt: string;
    setLlmUserPrompt: (value: string) => void;
    handleGenerateCharacterResponse: () => Promise<void>;
    isGeneratingResponse: boolean;
    llmResponse: string | null;
    llmError: string | null;
    // Future: Add chatHistory: Array<{speaker: 'user' | 'ai', text: string}> if implementing history
}

const CharacterChatPanel: React.FC<CharacterChatPanelProps> = ({
    characterName,
    isOpen,
    onClose,
    llmUserPrompt,
    setLlmUserPrompt,
    handleGenerateCharacterResponse,
    isGeneratingResponse,
    llmResponse,
    llmError,
}) => {
    if (!isOpen) {
        return null;
    }

    const panelTitle = `Chat with ${characterName}`;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleGenerateCharacterResponse();
    };

    return (
        <div
            className="character-chat-panel visible" // 'visible' class controls actual display via CSS
            role="dialog"
            aria-labelledby="character-chat-panel-title"
            aria-modal="true"
        >
            <div className="character-chat-panel-content-wrapper">
                <div className="character-chat-panel-header">
                    <span id="character-chat-panel-title" className="character-chat-panel-title">
                        {panelTitle}
                    </span>
                    <button
                        onClick={onClose}
                        className="character-chat-panel-close-button"
                        aria-label="Close chat panel"
                    >
                        &times;
                    </button>
                </div>

                <div className="character-chat-panel-messages-area">
                    {/*
                        In a future iteration, this area would display a list of messages (chat history).
                        For now, it will just display the latest AI response.
                    */}
                    {llmResponse && (
                        <div className="chat-message ai-message">
                            <strong>{characterName} responds:</strong>
                            <p style={{ whiteSpace: 'pre-wrap' }}>{llmResponse}</p>
                        </div>
                    )}
                    {llmError && (
                        <div className="chat-message error-message">
                            <p style={{ color: 'red' }}>Error: {llmError}</p>
                        </div>
                    )}
                    {isGeneratingResponse && !llmResponse && ( // Show loading only if there's no previous response displayed
                        <div className="chat-loading-indicator">
                            <LoadingSpinner />
                            <p>Thinking...</p>
                        </div>
                    )}
                </div>

                <div className="character-chat-panel-input-area">
                    <form onSubmit={handleSubmit} className="chat-input-form">
                        <textarea
                            id="llmUserChatPrompt"
                            className="form-control chat-textarea"
                            rows={3}
                            value={llmUserPrompt}
                            onChange={(e) => setLlmUserPrompt(e.target.value)}
                            placeholder={`Ask ${characterName} anything...`}
                            disabled={isGeneratingResponse}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary btn-sm send-chat-button"
                            disabled={isGeneratingResponse || !llmUserPrompt.trim()}
                        >
                            {isGeneratingResponse ? <LoadingSpinner /> : 'Send'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default CharacterChatPanel;
