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
}

const DEFAULT_AVATAR = '/logo_placeholder.svg'; // A default placeholder

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

    const getAvatar = (sender: string) => {
        if (sender === 'user') {
            return currentUserAvatar || DEFAULT_AVATAR;
        }
        // For LLM/character messages, use characterImage
        return characterImage || DEFAULT_AVATAR;
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
                    <button
                        onClick={onClose}
                        className="character-chat-panel-close-button"
                        aria-label="Close chat panel"
                    >
                        &times;
                    </button>
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
                            key={msg.id} // Use message ID as key
                            className={`chat-message-row ${
                                msg.sender === 'user' ? 'user-message-row' : 'ai-message-row'
                            }`}
                        >
                            <img
                                src={getAvatar(msg.sender)}
                                alt={msg.sender}
                                className="chat-avatar"
                            />
                            <div className={`chat-message-bubble ${msg.sender === 'user' ? 'user-message-bubble' : 'ai-message-bubble'}`}>
                                {msg.sender !== 'user' && (
                                    <strong className="message-sender-name">{msg.sender}:</strong>
                                )}
                                <p className="message-text">{msg.text}</p>
                                <span className="message-timestamp">
                                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        </div>
                    ))}
                    {isGeneratingResponse && !chatLoading && ( // Only show "thinking" if not loading history
                        <div className="chat-loading-indicator">
                             <img src={characterImage || DEFAULT_AVATAR} alt="loading" className="chat-avatar" />
                            <div className="chat-message-bubble ai-message-bubble">
                                <LoadingSpinner size="sm" />
                                <span className="message-text-italic"> {characterName} is thinking...</span>
                            </div>
                        </div>
                    )}
                     {llmError && !isGeneratingResponse && ( // Only show error if not currently generating
                        <div className="chat-message-row error-message-row">
                             <img src={getAvatar('system')} alt="error" className="chat-avatar" />
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
