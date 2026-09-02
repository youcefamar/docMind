import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Platform,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import Markdown from 'react-native-markdown-display';
import { colors, fontSize, radii, spacing } from '../lib/theme';
import { Citation, Source, SourceCard } from './SourceCard';
export type { Citation, Source };

export interface MessageBubbleProps {
  sender: 'user' | 'bot';
  content: string;
  timestamp?: string;
  sources?: Source[];
  citations?: Citation[];
  confidenceScore?: number;
  confidenceLabel?: string;
  isLoading?: boolean;
}

function LoadingDots() {
  const dot1 = useRef(new Animated.Value(0.3)).current;
  const dot2 = useRef(new Animated.Value(0.3)).current;
  const dot3 = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const createPulse = (value: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(value, {
            toValue: 1,
            duration: 400,
            useNativeDriver: true,
          }),
          Animated.timing(value, {
            toValue: 0.3,
            duration: 400,
            useNativeDriver: true,
          }),
        ])
      );

    const a1 = createPulse(dot1, 0);
    const a2 = createPulse(dot2, 200);
    const a3 = createPulse(dot3, 400);

    a1.start();
    a2.start();
    a3.start();

    return () => {
      a1.stop();
      a2.stop();
      a3.stop();
    };
  }, [dot1, dot2, dot3]);

  return (
    <View style={styles.loadingContainer}>
      <Animated.View style={[styles.loadingDot, { opacity: dot1 }]} />
      <Animated.View style={[styles.loadingDot, { opacity: dot2 }]} />
      <Animated.View style={[styles.loadingDot, { opacity: dot3 }]} />
    </View>
  );
}

const markdownStyles = {
  body: {
    color: colors.ink,
    fontSize: fontSize.base,
    lineHeight: 22,
  },
  heading1: {
    fontSize: fontSize.xl,
    fontWeight: '700' as const,
    color: colors.ink,
    marginVertical: 6,
  },
  heading2: {
    fontSize: fontSize.lg,
    fontWeight: '600' as const,
    color: colors.ink,
    marginVertical: 4,
  },
  heading3: {
    fontSize: fontSize.base,
    fontWeight: '600' as const,
    color: colors.ink,
    marginVertical: 4,
  },
  paragraph: {
    marginTop: 0,
    marginBottom: 6,
    lineHeight: 22,
  },
  code_inline: {
    backgroundColor: '#f1f3f4',
    color: '#0f172a',
    borderRadius: radii.sm,
    paddingHorizontal: 6,
    paddingVertical: 2,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: fontSize.sm,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  code_block: {
    backgroundColor: '#1e293b',
    color: '#f8fafc',
    borderRadius: radii.md,
    padding: spacing.md,
    marginVertical: spacing.sm,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: fontSize.sm,
  },
  fence: {
    backgroundColor: '#1e293b',
    color: '#f8fafc',
    borderRadius: radii.md,
    padding: spacing.md,
    marginVertical: spacing.sm,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: fontSize.sm,
  },
  bullet_list: {
    marginVertical: 4,
  },
  ordered_list: {
    marginVertical: 4,
  },
  bullet_list_item: {
    marginVertical: 2,
  },
  ordered_list_item: {
    marginVertical: 2,
  },
  strong: {
    fontWeight: '700' as const,
    color: colors.ink,
  },
  em: {
    fontStyle: 'italic' as const,
  },
  table: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radii.sm,
    marginVertical: spacing.sm,
  },
  th: {
    backgroundColor: '#f8fafc',
    padding: 6,
    fontWeight: '600' as const,
  },
  td: {
    padding: 6,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
};

export function MessageBubble({
  sender,
  content,
  timestamp,
  sources = [],
  citations = [],
  confidenceLabel,
  isLoading = false,
}: MessageBubbleProps) {
  const isUser = sender === 'user';

  return (
    <View style={[styles.wrapper, isUser ? styles.userWrapper : styles.botWrapper]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.botBubble]}>
        {isLoading ? (
          <LoadingDots />
        ) : isUser ? (
          <Text style={styles.userText}>{content}</Text>
        ) : (
          <View style={styles.botContent}>
            <Markdown style={markdownStyles}>{content}</Markdown>

            {confidenceLabel ? (
              <View style={styles.confidenceRow}>
                <View style={styles.confidenceDot} />
                <Text style={styles.confidenceText}>{confidenceLabel}</Text>
              </View>
            ) : null}

            {sources.length > 0 ? (
              <SourceCard sources={sources} citations={citations} />
            ) : null}
          </View>
        )}

        {timestamp && !isLoading ? (
          <Text style={[styles.time, isUser ? styles.userTime : styles.botTime]}>
            {timestamp}
          </Text>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginVertical: spacing.xs,
    paddingHorizontal: spacing.lg,
  },
  userWrapper: {
    alignItems: 'flex-end',
  },
  botWrapper: {
    alignItems: 'flex-start',
  },
  bubble: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderRadius: radii.lg,
  },
  userBubble: {
    backgroundColor: colors.ink,
    borderBottomRightRadius: 4,
    maxWidth: '82%',
  },
  botBubble: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
    borderBottomLeftRadius: 4,
    maxWidth: '92%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  userText: {
    color: '#ffffff',
    fontSize: fontSize.base,
    lineHeight: 22,
  },
  botContent: {
    width: '100%',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  loadingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.ink,
  },
  confidenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: spacing.xs,
  },
  confidenceDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.success,
  },
  confidenceText: {
    fontSize: fontSize.xs,
    color: colors.muted,
    fontWeight: '500',
  },
  time: {
    fontSize: fontSize.xs,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  userTime: {
    color: 'rgba(255, 255, 255, 0.65)',
  },
  botTime: {
    color: colors.muted,
  },
});
