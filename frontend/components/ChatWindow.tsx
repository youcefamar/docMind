'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Trash2, Sparkles, Filter, RefreshCw, CheckCircle2, Cpu, Database } from 'lucide-react';
import SourceCard, { Source } from './SourceCard';

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

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-1',
      sender: 'bot',
      content: 'Hello! I am **DocMind**, your internal AI knowledge assistant. Ask me anything about company policies, technical docs, or finance guidelines and I will provide exact answers with source citations.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);

  const [input, setInput] = useState('');
  const [categories, setCategories] = useState<string[]>(['All']);
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([]);
  const [retrievalProfiles, setRetrievalProfiles] = useState<string[]>(['fast']);
  const [selectedProfile, setSelectedProfile] = useState('fast');
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    fetch('/api/backend/config/')
      .then((res) => (res.ok ? res.json() : null))
      .then((config) => {
        if (!config) return;
        setCategories(config.category_filter_options || ['All']);
        setSuggestedPrompts(config.suggested_prompts || []);
        setRetrievalProfiles(config.retrieval_profiles || ['fast']);
        setSelectedCategory((current) => current || config.default_category || 'All');
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
      // Format chat history for multi-turn context
      const formattedHistory = messages
        .filter((m) => m.id !== 'welcome-1')
        .map((m) => ({
          sender: m.sender,
          content: m.content,
        }));

      const res = await fetch('/api/backend/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: query,
          category: selectedCategory,
          retrieval_profile: selectedProfile,
          chat_history: formattedHistory,
        }),
      });

      if (!res.ok) {
        const errorPayload = await res.json().catch(() => null);
        throw new Error(errorPayload?.detail || `Server returned HTTP ${res.status}`);
      }

      const data = await res.json();

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
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMsg: Message = {
        id: `err_${Date.now()}`,
        sender: 'bot',
        content: `⚠️ Unable to retrieve an answer right now. Please verify the backend FastAPI server is running. (${err.message})`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome-1',
        sender: 'bot',
        content: 'Session cleared. Ask a new question to query the knowledge base!',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] max-w-5xl mx-auto glass-panel rounded-2xl overflow-hidden shadow-2xl border border-gray-800">
      
      {/* Top Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-6 py-4 bg-gray-900/80 border-b border-gray-800 gap-4">
        {/* Category Filters */}
        <div className="flex items-center gap-2 overflow-x-auto py-1 no-scrollbar">
          <Filter className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          <span className="text-xs text-gray-400 font-medium mr-1">Filter:</span>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                selectedCategory === cat
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'bg-gray-800/60 text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="retrieval-profile" className="text-gray-400">Retrieval:</label>
          <select
            id="retrieval-profile"
            value={selectedProfile}
            onChange={(event) => setSelectedProfile(event.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-900 px-2 py-1.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
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

        <div className="flex items-center gap-2 text-[11px] text-gray-400">
          <Cpu className="h-3.5 w-3.5 text-indigo-400" />
          <span>{runtimeStatus?.llm_ready ? runtimeStatus.llm_model : 'Local model not loaded'}</span>
          <Database className={`h-3.5 w-3.5 ${runtimeStatus?.dense_index_ready ? 'text-emerald-400' : 'text-amber-400'}`} />
          <span>{runtimeStatus?.dense_index_ready ? 'Index ready' : 'Indexing required'}</span>
        </div>

        {/* Clear Chat Action */}
        <button
          onClick={handleClearChat}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          title="Clear Session History"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Chat</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';

          return (
            <div
              key={msg.id}
              className={`flex gap-4 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
                  isUser
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gradient-to-tr from-indigo-500 to-indigo-700 text-white'
                }`}
              >
                {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>

              {/* Message Content Bubble */}
              <div className={`space-y-2 max-w-full ${isUser ? 'text-right' : 'text-left'}`}>
                
                {/* Meta header */}
                <div className={`flex items-center gap-2 text-[11px] text-gray-400 ${isUser ? 'justify-end' : ''}`}>
                  <span className="font-semibold text-gray-300">
                    {isUser ? 'You' : 'DocMind Assistant'}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>

                  {/* Confidence Indicator Tag */}
                  {!isUser && msg.confidenceLabel && (
                    <span
                      className={`ml-2 px-2 py-0.5 rounded-full font-semibold text-[10px] border flex items-center gap-1 ${
                        msg.confidenceLabel === 'High'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : msg.confidenceLabel === 'Medium'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-red-500/10 text-red-400 border-red-500/30'
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
                      ? 'bg-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-600/20'
                      : 'glass-card text-gray-100 rounded-tl-none border border-gray-800'
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
            <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 animate-pulse">
              <Bot className="w-5 h-5" />
            </div>
            <div className="glass-card p-4 rounded-2xl rounded-tl-none border border-gray-800 text-sm text-indigo-300 flex items-center gap-3">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Searching vectorized documents & synthesizing answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Suggestions (Shown if only welcome message present) */}
      {messages.length <= 1 && (
        <div className="px-6 py-2">
          <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Try asking:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {suggestedPrompts.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handleSend(prompt)}
                className="text-left text-xs bg-gray-900/60 hover:bg-gray-800 text-gray-300 hover:text-white p-2.5 rounded-xl border border-gray-800 transition-all truncate"
              >
                "{prompt}"
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form Bar */}
      <div className="p-4 bg-gray-900/90 border-t border-gray-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3 bg-gray-950 p-2 rounded-xl border border-gray-800 focus-within:border-indigo-500 transition-colors"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask a question in ${selectedCategory === 'All' ? 'all documents' : selectedCategory}...`}
            className="flex-1 bg-transparent px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-medium shadow-md shadow-indigo-600/30 transition-all flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-[11px] text-gray-500 text-center mt-2">
          DocMind grounds responses directly on indexed company PDFs with page citation verification.
        </p>
      </div>

    </div>
  );
}
