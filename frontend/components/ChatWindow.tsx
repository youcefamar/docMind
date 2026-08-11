'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Trash2, Sparkles, Filter, RefreshCw, CheckCircle2, Cpu, Database } from 'lucide-react';
import SourceCard, { Source } from './SourceCard';
import { getApiErrorMessage, readApiPayload } from '../lib/api';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  confidenceScore?: number;
  confidenceLabel?: string;
  sources?: Source[];
  citations?: Citation[];
  retrievalProfile?: string;
  timestamp: string;
}

interface Citation {
  source_id: string;
  filename: string;
  location_type: string;
  location_value: string;
  supported: boolean;
}

interface RuntimeStatus {
  embedding_ready: boolean;
  dense_index_ready: boolean;
  bm25_index_ready: boolean;
  quality_ready: boolean;
  llm_ready: boolean;
  llm_backend: string;
  llm_model: string;
}

const CHAT_SESSION_STORAGE_KEY = 'docmind.chat-session.v1';
const MAX_STORED_MESSAGES = 100;
const MAX_CHAT_HISTORY_MESSAGES = 8;
const MAX_CHAT_HISTORY_CHARACTERS = 1800;
const BACKEND_RETRY_DELAY_MS = 1200;

function createWelcomeMessage(content = 'Hello! I am **DocMind**, your internal AI knowledge assistant. Ask me anything about company policies, technical docs, or finance guidelines and I will provide exact answers with source citations.'): Message {
  return {
    id: 'welcome-1',
    sender: 'bot',
    content,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
}

function isStoredMessage(value: unknown): value is Message {
  if (!value || typeof value !== 'object') return false;
  const message = value as Record<string, unknown>;
  return (
    typeof message.id === 'string'
    && (message.sender === 'user' || message.sender === 'bot')
    && typeof message.content === 'string'
    && typeof message.timestamp === 'string'
  );
}

function restoreChatSession(): {
  messages: Message[];
  selectedProfile: string;
  selectedCategory: string;
} | null {
  try {
    const raw = window.localStorage.getItem(CHAT_SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    const session = parsed as Record<string, unknown>;
    if (session.version !== 1 || !Array.isArray(session.messages)) return null;

    const messages = session.messages.filter(isStoredMessage).slice(-MAX_STORED_MESSAGES);
    return {
      messages: messages.length > 0 ? messages : [createWelcomeMessage()],
      selectedProfile: typeof session.selectedProfile === 'string' ? session.selectedProfile : 'fast',
      selectedCategory: typeof session.selectedCategory === 'string' ? session.selectedCategory : 'All',
    };
  } catch (error) {
    console.warn('Unable to restore the local DocMind chat session:', error);
    return null;
  }
}

function buildChatHistory(messages: Message[]) {
  const recentMessages = messages
    .filter((message) => message.id !== 'welcome-1')
    .slice(-MAX_CHAT_HISTORY_MESSAGES);
  const history: Array<{ sender: Message['sender']; content: string }> = [];
  let remainingCharacters = MAX_CHAT_HISTORY_CHARACTERS;

  for (const message of [...recentMessages].reverse()) {
    if (remainingCharacters <= 0) break;
    const content = message.content.slice(-remainingCharacters);
    history.unshift({ sender: message.sender, content });
    remainingCharacters -= content.length;
  }

  return history;
}

function waitForBackendReload() {
  return new Promise<void>((resolve) => window.setTimeout(resolve, BACKEND_RETRY_DELAY_MS));
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>(() => [createWelcomeMessage()]);

  const [input, setInput] = useState('');
  const [categories, setCategories] = useState<string[]>(['All']);
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([]);
  const [retrievalProfiles, setRetrievalProfiles] = useState<string[]>(['fast']);
  const [selectedProfile, setSelectedProfile] = useState('fast');
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isLoading, setIsLoading] = useState(false);
  const [isChatSessionRestored, setIsChatSessionRestored] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const lastMessageId = messages.at(-1)?.id;

  useEffect(() => {
    if (lastMessageId || isLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: isLoading ? 'auto' : 'smooth' });
    }
  }, [lastMessageId, isLoading]);

  useEffect(() => {
    const savedSession = restoreChatSession();
    if (savedSession) {
      setMessages(savedSession.messages);
      setSelectedProfile(savedSession.selectedProfile);
      setSelectedCategory(savedSession.selectedCategory);
    }
    setIsChatSessionRestored(true);
  }, []);

  useEffect(() => {
    if (!isChatSessionRestored) return;
    try {
      window.localStorage.setItem(
        CHAT_SESSION_STORAGE_KEY,
        JSON.stringify({
          version: 1,
          messages: messages.slice(-MAX_STORED_MESSAGES),
          selectedProfile,
          selectedCategory,
        }),
      );
    } catch (error) {
      console.warn('Unable to save the local DocMind chat session:', error);
    }
  }, [isChatSessionRestored, messages, selectedCategory, selectedProfile]);

  useEffect(() => {
    fetch('/api/backend/config/')
      .then((res) => (res.ok ? res.json() : null))
      .then((config) => {
        if (!config) return;
        const categoryOptions = config.category_filter_options || ['All'];
        const profileOptions = config.retrieval_profiles || ['fast'];
        setCategories(categoryOptions);
        setSuggestedPrompts(config.suggested_prompts || []);
        setRetrievalProfiles(profileOptions);
        setSelectedCategory((current) => (
          categoryOptions.includes(current) ? current : config.default_category || 'All'
        ));
        setSelectedProfile((current) => (profileOptions.includes(current) ? current : 'fast'));
      })
      .catch((err) => console.error('Failed to fetch backend configuration:', err));

    const refreshRuntimeStatus = () => {
      fetch('/api/backend/runtime/status')
        .then((res) => (res.ok ? res.json() : null))
        .then((status) => {
          if (status) setRuntimeStatus(status);
        })
        .catch((err) => console.error('Failed to fetch runtime status:', err));
    };
    refreshRuntimeStatus();
    const interval = window.setInterval(refreshRuntimeStatus, 10000);
    return () => window.clearInterval(interval);
  }, []);

  const handleSend = async (customPrompt?: string) => {
    const query = customPrompt || input;
    if (!query.trim()) return;

    const userMsg: Message = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customPrompt) setInput('');
    setIsLoading(true);

    try {
      const requestBody = JSON.stringify({
        question: query,
        category: selectedCategory,
        retrieval_profile: selectedProfile,
        chat_history: buildChatHistory(messages),
      });
      const requestAnswer = () => fetch('/api/backend/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: requestBody,
      });
      let res = await requestAnswer();
      if (res.status === 503) {
        await waitForBackendReload();
        res = await requestAnswer();
      }

      if (!res.ok) {
        const errorPayload = await readApiPayload<unknown>(res);
        throw new Error(getApiErrorMessage(errorPayload, `Server returned HTTP ${res.status}`));
      }

      const data = await readApiPayload<Record<string, any>>(res);
      if (!data || typeof data.answer !== 'string') {
        throw new Error('Backend returned an invalid answer response.');
      }

      const botMsg: Message = {
        id: `bot_${Date.now()}`,
        sender: 'bot',
        content: data.answer,
        confidenceScore: data.confidence_score,
        confidenceLabel: data.confidence_label,
        sources: data.sources || [],
        citations: data.citations || [],
        retrievalProfile: data.retrieval_profile,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected chat error occurred.';
      console.warn('Chat request failed:', errorMessage);
      const errorMsg: Message = {
        id: `err_${Date.now()}`,
        sender: 'bot',
        content: `⚠️ ${errorMessage}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    try {
      window.localStorage.removeItem(CHAT_SESSION_STORAGE_KEY);
    } catch (error) {
      console.warn('Unable to clear the local DocMind chat session:', error);
    }
    setMessages([createWelcomeMessage('Session cleared. Ask a new question to query the knowledge base!')]);
  };

  return (
    <div className="flex h-[calc(100vh-6.5rem)] min-h-[620px] max-w-6xl flex-col overflow-hidden rounded-2xl border border-[#e8e8e5] bg-white shadow-[0_18px_50px_rgba(32,33,36,0.055)]">
      
      {/* Top Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#ededeb] bg-white px-5 py-4 sm:px-6">
        {/* Category Filters */}
        <div className="flex items-center gap-2 overflow-x-auto py-1 no-scrollbar">
          <Filter className="h-4 w-4 flex-shrink-0 text-slate-400" />
          <span className="mr-1 text-xs font-medium text-slate-500">Scope</span>
          {categories.map((cat) => (
            <button
              type="button"
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                selectedCategory === cat
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'border border-[#e8e8e5] bg-white text-slate-500 hover:border-slate-300 hover:text-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="retrieval-profile" className="text-slate-500">Retrieval</label>
          <select
            id="retrieval-profile"
            value={selectedProfile}
            onChange={(event) => setSelectedProfile(event.target.value)}
            className="rounded-lg border border-[#e3e3e0] bg-[#fafaf9] px-2.5 py-1.5 font-medium text-slate-700 focus:border-slate-400 focus:outline-none"
          >
            {retrievalProfiles.map((profile) => (
              <option
                key={profile}
                value={profile}
                disabled={profile === 'quality' && runtimeStatus !== null && !runtimeStatus.quality_ready}
              >
                {profile === 'quality' ? 'Quality' : 'Fast'}
                {profile === 'quality' && runtimeStatus !== null && !runtimeStatus.quality_ready ? ' (not ready)' : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-slate-500">
          <Cpu className="h-3.5 w-3.5 text-slate-400" />
          <span>{runtimeStatus?.llm_ready ? runtimeStatus.llm_model : 'Local model not loaded'}</span>
          <Database className={`h-3.5 w-3.5 ${runtimeStatus?.dense_index_ready ? 'text-emerald-500' : 'text-amber-500'}`} />
          <span>{runtimeStatus?.dense_index_ready ? 'Index ready' : 'Indexing required'}</span>
        </div>

        {/* Clear Chat Action */}
        <button
          type="button"
          onClick={handleClearChat}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-rose-50 hover:text-rose-600"
          title="Clear Session History"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Chat</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 space-y-7 overflow-y-auto bg-[#fcfcfb] p-5 sm:p-6">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';

          return (
            <div
              key={msg.id}
              className={`flex max-w-3xl gap-3.5 ${isUser ? 'ml-auto flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl shadow-sm ${
                  isUser
                    ? 'bg-slate-200 text-slate-600'
                    : 'bg-slate-900 text-white'
                }`}
              >
                {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>

              {/* Message Content Bubble */}
              <div className={`space-y-2 max-w-full ${isUser ? 'text-right' : 'text-left'}`}>
                
                {/* Meta header */}
                <div className={`flex items-center gap-2 text-[11px] text-slate-400 ${isUser ? 'justify-end' : ''}`}>
                  <span className="font-semibold text-slate-600">
                    {isUser ? 'You' : 'DocMind Assistant'}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>

                  {/* Confidence Indicator Tag */}
                  {!isUser && msg.confidenceLabel && (
                    <span
                      className={`ml-2 px-2 py-0.5 rounded-full font-semibold text-[10px] border flex items-center gap-1 ${
                        msg.confidenceLabel === 'High'
                          ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                          : msg.confidenceLabel === 'Medium'
                          ? 'border-amber-200 bg-amber-50 text-amber-700'
                          : 'border-rose-200 bg-rose-50 text-rose-700'
                      }`}
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Confidence: {msg.confidenceLabel}
                    </span>
                  )}
                </div>

                {/* Bubble Container */}
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'rounded-tr-none bg-slate-900 text-white shadow-sm'
                      : 'rounded-tl-none border border-[#e7e7e4] bg-white text-slate-700 shadow-[0_4px_14px_rgba(32,33,36,0.025)]'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>

                  {/* Sources Section if Bot */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <SourceCard sources={msg.sources} citations={msg.citations} />
                  )}
                </div>

              </div>
            </div>
          );
        })}

        {/* Loading Spinner Indicator */}
        {isLoading && (
          <div className="flex gap-4 max-w-3xl">
            <div className="flex h-9 w-9 flex-shrink-0 animate-pulse items-center justify-center rounded-xl bg-slate-900 text-white">
              <Bot className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-3 rounded-2xl rounded-tl-none border border-[#e7e7e4] bg-white p-4 text-sm text-slate-600 shadow-[0_4px_14px_rgba(32,33,36,0.025)]">
              <RefreshCw className="h-4 w-4 animate-spin text-slate-700" />
              <span>Searching vectorized documents & synthesizing answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Suggestions (Shown if only welcome message present) */}
      {messages.length <= 1 && (
        <div className="border-t border-[#f0f0ee] bg-white px-5 py-3 sm:px-6">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-500">
            <Sparkles className="h-3.5 w-3.5 text-slate-400" />
            Try asking:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {suggestedPrompts.map((prompt) => (
              <button
                type="button"
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="truncate rounded-xl border border-[#e6e6e3] bg-[#fafaf9] p-2.5 text-left text-xs text-slate-600 transition-all hover:border-slate-300 hover:bg-white hover:text-slate-900"
              >
                "{prompt}"
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form Bar */}
      <div className="border-t border-[#ededeb] bg-white p-4 sm:px-6">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3 rounded-xl border border-[#dededb] bg-[#fafaf9] p-2 shadow-[0_3px_10px_rgba(32,33,36,0.025)] transition-colors focus-within:border-slate-400 focus-within:bg-white"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask a question in ${selectedCategory === 'All' ? 'all documents' : selectedCategory}...`}
            className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="flex-shrink-0 rounded-lg bg-slate-900 p-2.5 font-medium text-white shadow-sm transition-all hover:bg-slate-700 disabled:opacity-40"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="mt-2 text-center text-[11px] text-slate-400">
          DocMind grounds responses directly on indexed company PDFs with page citation verification.
        </p>
      </div>

    </div>
  );
}
