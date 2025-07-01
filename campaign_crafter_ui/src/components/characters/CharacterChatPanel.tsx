import React, { useEffect, useRef } from 'react'; // Added useEffect, useRef
import LoadingSpinner from '../common/LoadingSpinner';
import './CharacterChatPanel.css';

// Define ChatMessage interface
export interface ChatMessage {
    speaker: string; // 'user', or characterName for AI responses
    text: string;
}

export interface CharacterChatPanelProps {
    characterName: string;
    isOpen: boolean;
    onClose: () => void;
    llmUserPrompt: string;
    setLlmUserPrompt: (value: string) => void;
    handleGenerateCharacterResponse: () => Promise<void>;
    isGeneratingResponse: boolean;
    llmResponse: string | null; // This will likely be removed or handled by parent adding to chatHistory
    llmError: string | null;
    chatHistory: Array<ChatMessage>; // Added chatHistory
    // setChatHistory is managed by the parent component
}

const CharacterChatPanel: React.FC<CharacterChatPanelProps> = ({
    characterName,
    isOpen,
    onClose,
    llmUserPrompt,
    setLlmUserPrompt,
    handleGenerateCharacterResponse,
    isGeneratingResponse,
    llmResponse, // Keep for now, but ideally this becomes part of chatHistory via parent
    llmError,
    chatHistory, // Added chatHistory
}) => {
    const messagesContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
    }, [chatHistory, isGeneratingResponse, llmError, llmResponse]); // Scroll on new messages or status changes

    if (!isOpen) {
        return null;
    }

    const panelTitle = `Chat with ${characterName}`;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // User's message is added to chatHistory by the parent component
        // inside handleGenerateCharacterResponse or its wrapper.
        handleGenerateCharacterResponse();
    };

    return (
        <div
            className="character-chat-panel visible"
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

                <div className="character-chat-panel-messages-area" ref={messagesContainerRef}>
                    {chatHistory.map((msg, index) => (
                        <div
                            key={index}
                            className={`chat-message ${
                                msg.speaker === 'user' ? 'user-message' : 'ai-message'
                            }`}
                        >
                            {msg.speaker !== 'user' && (
                                <strong>{msg.speaker}:</strong>
                            )}
                            <p style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</p>
                        </div>
                    ))}
                    {/* Displaying llmResponse directly here is temporary if parent doesn't immediately add to history */}
                    {/* This should ideally be handled by parent adding to chatHistory */}
                    {/* {llmResponse && !chatHistory.find(msg => msg.text === llmResponse && msg.speaker === characterName) && (
                        <div className="chat-message ai-message">
                            <strong>{characterName}:</strong>
                            <p style={{ whiteSpace: 'pre-wrap' }}>{llmResponse}</p>
                        </div>
                    )} */}
                    {isGeneratingResponse && (
                        <div className="chat-loading-indicator">
                            <LoadingSpinner />
                            <p>{characterName} is thinking...</p>
                        </div>
                    )}
                     {llmError && (
                        <div className="chat-message error-message">
                            <p>Error: {llmError}</p>
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
