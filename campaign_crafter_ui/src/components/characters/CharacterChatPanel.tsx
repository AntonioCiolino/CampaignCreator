import React, { useEffect, useRef } from 'react';
import LoadingSpinner from '../common/LoadingSpinner';
import { ChatMessage } from '../../types/characterTypes'; // Corrected path
import './CharacterChatPanel.css';

// ChatMessage interface is now imported from characterTypes

export interface CharacterChatPanelProps {
    characterName: string;
    characterImage?: string; // For character avatar
    currentUserAvatar?: string; // For user avatar
    isOpen: boolean;
    onClose: () => void;
    llmUserPrompt: string;
    setLlmUserPrompt: (value: string) => void;
    handleGenerateCharacterResponse: () => Promise<void>;
    isGeneratingResponse: boolean;
    llmError: string | null; // Combined error from parent
    chatHistory: Array<ChatMessage>;
    chatLoading: boolean; // For loading history
    handleClearChat: () => Promise<void>;
    onMemorySummaryOpen: () => void;
}

const DEFAULT_AVATAR = '/logo_placeholder.svg';

const CharacterChatPanel: React.FC<CharacterChatPanelProps> = ({
    characterName,
    characterImage,
    currentUserAvatar,
    isOpen,
    onClose,
    llmUserPrompt,
    setLlmUserPrompt,
    handleGenerateCharacterResponse,
    isGeneratingResponse,
    llmError,
    chatHistory,
    chatLoading,
    handleClearChat,
    onMemorySummaryOpen,
}) => {
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null); // Ref for textarea

    useEffect(() => {
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
    }, [chatHistory, isGeneratingResponse, llmError]);

    // Focus textarea when panel opens
    useEffect(() => {
        if (isOpen && textareaRef.current) {
            textareaRef.current.focus();
        }
    }, [isOpen]);

    if (!isOpen) {
        return null;
    }

    const panelTitle = `Chat with ${characterName}`;

    const handleSubmit = (e?: React.FormEvent) => { // Make event optional for Enter key
        if (e) e.preventDefault();
        if (!llmUserPrompt.trim() || isGeneratingResponse) return;
        handleGenerateCharacterResponse();
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    // getAvatar function is no longer strictly needed if ChatMessage objects are pre-enriched with avatar URLs.
    // However, it's used for the error message avatar, so let's keep a simplified version or handle it directly.
    const getSystemAvatar = () => { // For system messages like errors
        return DEFAULT_AVATAR; // Or a specific system/error icon
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
                    <img src={characterImage || DEFAULT_AVATAR} alt={characterName} className="chat-header-avatar" />
                    <span id="character-chat-panel-title" className="character-chat-panel-title">
                        {panelTitle}
                    </span>
                    <div>
                        <button
                            onClick={onMemorySummaryOpen}
                            className="btn btn-info btn-sm me-2"
                            aria-label="View memory summary"
                        >
                            Summary
                        </button>
                        <button
                            onClick={handleClearChat}
                            className="btn btn-secondary btn-sm me-2"
                            aria-label="Clear chat history"
                            disabled={isGeneratingResponse || chatLoading}
                        >
                            Clear Chat
                        </button>
                        <button
                            onClick={onClose}
                            className="character-chat-panel-close-button"
                            aria-label="Close chat panel"
                        >
                            &times;
                        </button>
                    </div>
                </div>

                <div className="character-chat-panel-messages-area" ref={messagesContainerRef}>
                    {chatLoading && (
                        <div className="chat-loading-indicator">
                            <LoadingSpinner />
                            <p>Loading history...</p>
                        </div>
                    )}
                    {!chatLoading && chatHistory.map((msg) => (
                        <div
                            key={msg.uiKey || msg.timestamp} // Use uiKey (preferred) or fallback to timestamp if uiKey not present
                            className={`chat-message-row ${
                                msg.senderType === 'user' ? 'user-message-row' : 'ai-message-row'
                            }`}
                        >
                            <img
                                // Use pre-enriched avatar URLs from the ChatMessage object
                                src={msg.senderType === 'user' ? (msg.user_avatar_url || DEFAULT_AVATAR) : (msg.character_avatar_url || DEFAULT_AVATAR)}
                                alt={msg.senderType === 'user' ? 'User' : characterName} // Corrected alt text logic
                                className="chat-avatar"
                            />
                            <div className={`chat-message-bubble ${msg.senderType === 'user' ? 'user-message-bubble' : 'ai-message-bubble'}`}>
                                {msg.senderType !== 'user' && (
                                    // Display characterName for AI messages
                                    <strong className="message-sender-name">{characterName}:</strong>
                                )}
                                <p className="message-text">{msg.text}</p>
                                <span className="message-timestamp">
                                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        </div>
                    ))}
                    {isGeneratingResponse && !chatLoading && ( // Only show "thinking" if not loading history
                        <div className="chat-message-row ai-message-row thinking-indicator-row"> {/* Use standard row classes */}
                            <img
                                src={characterImage || DEFAULT_AVATAR}
                                alt={`${characterName} thinking`} // More descriptive alt text
                                className="chat-avatar"
                            />
                            <div className="chat-message-bubble ai-message-bubble"> {/* Bubble for spinner and text */}
                                <LoadingSpinner size="sm" inline={true} /> {/* Ensure spinner can be inline */}
                                <span className="message-text-italic"> {characterName} is thinking...</span>
                            </div>
                        </div>
                    )}
                     {llmError && !isGeneratingResponse && ( // Only show error if not currently generating
                        <div className="chat-message-row error-message-row">
                             <img src={getSystemAvatar()} alt="error" className="chat-avatar" />
                             <div className="chat-message-bubble error-bubble">
                                <p>Error: {llmError}</p>
                             </div>
                        </div>
                    )}
                </div>

                <div className="character-chat-panel-input-area">
                    <form onSubmit={handleSubmit} className="chat-input-form">
                        <textarea
                            ref={textareaRef} // Assign ref
                            id="llmUserChatPrompt"
                            className="form-control chat-textarea"
                            rows={2} // Adjusted default rows
                            value={llmUserPrompt}
                            onChange={(e) => setLlmUserPrompt(e.target.value)}
                            onKeyDown={handleKeyDown} // Added Enter key handler
                            placeholder={`Message ${characterName}...`}
                            disabled={isGeneratingResponse || chatLoading}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary btn-sm send-chat-button"
                            disabled={isGeneratingResponse || chatLoading || !llmUserPrompt.trim()}
                        >
                            {isGeneratingResponse ? <LoadingSpinner size="sm" inline={true} /> : 'Send'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default CharacterChatPanel;
