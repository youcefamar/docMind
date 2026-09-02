import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { apiFetch, getApiErrorMessage, readApiPayload } from '../../lib/api';
import { colors, fontSize, radii, spacing } from '../../lib/theme';
import { ChatInput } from '../../components/ChatInput';
import { ConfirmSheet } from '../../components/ConfirmSheet';
import { Citation, MessageBubble, Source } from '../../components/MessageBubble';
import { ProfileChips } from '../../components/ProfileChips';
import { StatusDot } from '../../components/StatusDot';

export interface Message {
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

interface RuntimeStatus {
  llm_ready: boolean;
  llm_backend?: string;
  llm_model?: string;
}

interface PublicConfig {
  categories?: string[];
  category_filter_options?: string[];
  default_category?: string;
  suggested_prompts?: string[];
}

const CHAT_SESSION_STORAGE_KEY = 'docmind.chat-session.v1';
const MAX_STORED_MESSAGES = 100;
const MAX_CHAT_HISTORY_MESSAGES = 8;
const MAX_CHAT_HISTORY_CHARACTERS = 1800;
const BACKEND_RETRY_DELAY_MS = 1200;

function createWelcomeMessage(
  content = 'Hello! I am **DocMind**, your internal offline AI knowledge assistant. Ask me anything about company documents, technical specs, or policies and I will provide exact grounded answers with citations.'
): Message {
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
    typeof message.id === 'string' &&
    (message.sender === 'user' || message.sender === 'bot') &&
    typeof message.content === 'string' &&
    typeof message.timestamp === 'string'
  );
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

export default function ChatScreen() {
  const insets = useSafeAreaInsets();
  const flatListRef = useRef<FlatList<Message>>(null);

  const [messages, setMessages] = useState<Message[]>([createWelcomeMessage()]);
  const [selectedProfile, setSelectedProfile] = useState<'fast' | 'quality'>('fast');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [categories, setCategories] = useState<string[]>(['All']);
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([]);
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSessionLoaded, setIsSessionLoaded] = useState(false);
  const [isConfirmClearVisible, setIsConfirmClearVisible] = useState(false);

  // Restore saved session on mount
  useEffect(() => {
    async function loadSession() {
      try {
        const raw = await AsyncStorage.getItem(CHAT_SESSION_STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && Array.isArray(parsed.messages)) {
            const valid = parsed.messages.filter(isStoredMessage).slice(-MAX_STORED_MESSAGES);
            if (valid.length > 0) {
              setMessages(valid);
            }
            if (parsed.selectedProfile === 'fast' || parsed.selectedProfile === 'quality') {
              setSelectedProfile(parsed.selectedProfile);
            }
            if (typeof parsed.selectedCategory === 'string') {
              setSelectedCategory(parsed.selectedCategory);
            }
          }
        }
      } catch (err) {
        console.warn('Unable to restore chat session:', err);
      } finally {
        setIsSessionLoaded(true);
      }
    }
    loadSession();
  }, []);

  // Save session when messages or settings change
  useEffect(() => {
    if (!isSessionLoaded) return;
    async function persistSession() {
      try {
        await AsyncStorage.setItem(
          CHAT_SESSION_STORAGE_KEY,
          JSON.stringify({
            version: 1,
            messages: messages.slice(-MAX_STORED_MESSAGES),
            selectedProfile,
            selectedCategory,
          })
        );
      } catch (err) {
        console.warn('Unable to persist chat session:', err);
      }
    }
    persistSession();
  }, [isSessionLoaded, messages, selectedProfile, selectedCategory]);

  // Load config & runtime status
  const loadStatus = useCallback(async () => {
    try {
      const [configRes, statusRes] = await Promise.allSettled([
        apiFetch('/api/config/'),
        apiFetch('/api/runtime/status'),
      ]);

      if (configRes.status === 'fulfilled' && configRes.value.ok) {
        const config = await readApiPayload<PublicConfig>(configRes.value);
        if (config) {
          const options = config.category_filter_options || ['All'];
          setCategories(options);
          setSuggestedPrompts(config.suggested_prompts || []);
        }
      }

      if (statusRes.status === 'fulfilled' && statusRes.value.ok) {
        const status = await readApiPayload<RuntimeStatus>(statusRes.value);
        if (status) {
          setRuntimeStatus(status);
        }
      }
    } catch {
      // Backend unreachable or loading
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  // Auto-scroll when messages change or loading starts
  useEffect(() => {
    const timer = setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
    return () => clearTimeout(timer);
  }, [messages.length, isLoading]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      id: `user_${Date.now()}`,
      sender: 'user',
      content: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const body = {
        question: text.trim(),
        category: selectedCategory,
        chat_history: buildChatHistory(messages),
        retrieval_profile: selectedProfile,
      };

      const executeRequest = () =>
        apiFetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

      let res = await executeRequest();

      // Retry once if 503 (model warming up / reindexing)
      if (res.status === 503) {
        await new Promise((r) => setTimeout(r, BACKEND_RETRY_DELAY_MS));
        res = await executeRequest();
      }

      if (!res.ok) {
        const payload = await readApiPayload<unknown>(res);
        throw new Error(getApiErrorMessage(payload, `Server returned HTTP ${res.status}`));
      }

      const data = await readApiPayload<Record<string, any>>(res);
      if (!data || typeof data.answer !== 'string') {
        throw new Error('Server returned an invalid answer.');
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
      const errMessage =
        err instanceof Error ? err.message : 'An unexpected error occurred.';
      const errorMsg: Message = {
        id: `err_${Date.now()}`,
        sender: 'bot',
        content: `⚠️ ${errMessage}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    setIsConfirmClearVisible(false);
    try {
      await AsyncStorage.removeItem(CHAT_SESSION_STORAGE_KEY);
    } catch (err) {
      console.warn('Unable to clear chat session:', err);
    }
    setMessages([
      createWelcomeMessage(
        'Session cleared. Ask a question to query the DocMind knowledge base!'
      ),
    ]);
  };

  const showSuggestedPrompts =
    messages.length <= 1 && suggestedPrompts.length > 0 && !isLoading;

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.logoBadge}>
            <Feather name="cpu" size={16} color="#ffffff" />
          </View>
          <Text style={styles.headerTitle}>DocMind</Text>
        </View>

        <View style={styles.headerRight}>
          <StatusDot
            ready={Boolean(runtimeStatus?.llm_ready)}
            loading={runtimeStatus === null}
          />
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setIsConfirmClearVisible(true)}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            accessibilityLabel="Clear chat history"
          >
            <Feather name="trash-2" size={18} color={colors.muted} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Category Filter Chips (if more than 1) */}
      {categories.length > 1 ? (
        <View style={styles.categoryBar}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoryScroll}
          >
            <Feather name="filter" size={13} color={colors.muted} style={styles.filterIcon} />
            {categories.map((cat) => {
              const isSelected = selectedCategory === cat;
              return (
                <TouchableOpacity
                  key={cat}
                  style={[
                    styles.categoryChip,
                    isSelected ? styles.categoryChipActive : styles.categoryChipInactive,
                  ]}
                  onPress={() => setSelectedCategory(cat)}
                >
                  <Text
                    style={[
                      styles.categoryChipText,
                      isSelected
                        ? styles.categoryChipTextActive
                        : styles.categoryChipTextInactive,
                    ]}
                  >
                    {cat}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      ) : null}

      {/* Messages List */}
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <MessageBubble
              sender={item.sender}
              content={item.content}
              timestamp={item.timestamp}
              sources={item.sources}
              citations={item.citations}
              confidenceScore={item.confidenceScore}
              confidenceLabel={item.confidenceLabel}
            />
          )}
          contentContainerStyle={[
            styles.listContent,
            { paddingBottom: spacing.md },
          ]}
          ListFooterComponent={
            <>
              {isLoading ? (
                <MessageBubble sender="bot" content="" isLoading={true} />
              ) : null}

              {showSuggestedPrompts ? (
                <View style={styles.suggestionsContainer}>
                  <Text style={styles.suggestionsTitle}>Suggested Prompts</Text>
                  <View style={styles.suggestionsList}>
                    {suggestedPrompts.map((prompt, idx) => (
                      <TouchableOpacity
                        key={idx}
                        style={styles.suggestionChip}
                        onPress={() => handleSendMessage(prompt)}
                        activeOpacity={0.7}
                      >
                        <Feather name="help-circle" size={13} color={colors.muted} />
                        <Text style={styles.suggestionText}>{prompt}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              ) : null}
            </>
          }
        />

        {/* Profile Selector + Chat Input */}
        <View style={[styles.bottomArea, { paddingBottom: Math.max(insets.bottom, 8) }]}>
          <ProfileChips
            selected={selectedProfile}
            onChange={setSelectedProfile}
          />
          <ChatInput
            onSend={handleSendMessage}
            disabled={isLoading}
          />
        </View>
      </KeyboardAvoidingView>

      {/* Clear Confirmation Modal */}
      <ConfirmSheet
        visible={isConfirmClearVisible}
        title="Clear conversation?"
        message="This will reset your conversation history. Verified sources and document indexes will remain intact."
        confirmText="Clear Chat"
        isDestructive={true}
        onConfirm={handleClearHistory}
        onCancel={() => setIsConfirmClearVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  flex: {
    flex: 1,
  },
  header: {
    height: 56,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  logoBadge: {
    width: 30,
    height: 30,
    borderRadius: radii.sm,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: fontSize.xl,
    fontWeight: '700',
    color: colors.ink,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  headerButton: {
    padding: 4,
  },
  categoryBar: {
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    paddingVertical: 6,
  },
  categoryScroll: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    gap: 6,
  },
  filterIcon: {
    marginRight: 2,
  },
  categoryChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: radii.pill,
  },
  categoryChipActive: {
    backgroundColor: colors.chipActive,
  },
  categoryChipInactive: {
    backgroundColor: colors.chipInactive,
  },
  categoryChipText: {
    fontSize: fontSize.xs,
    fontWeight: '600',
  },
  categoryChipTextActive: {
    color: '#ffffff',
  },
  categoryChipTextInactive: {
    color: colors.chipInactiveText,
  },
  listContent: {
    paddingTop: spacing.md,
  },
  suggestionsContainer: {
    marginTop: spacing.lg,
    paddingHorizontal: spacing.lg,
  },
  suggestionsTitle: {
    fontSize: fontSize.xs,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: spacing.sm,
  },
  suggestionsList: {
    gap: spacing.xs,
  },
  suggestionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
  },
  suggestionText: {
    fontSize: fontSize.sm,
    color: colors.ink,
    flex: 1,
  },
  bottomArea: {
    backgroundColor: colors.surface,
  },
});
