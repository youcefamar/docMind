import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface Source {
  doc_id: string;
  chunk_id?: string;
  filename: string;
  category: string;
  page_number: number;
  total_pages: number;
  excerpt: string;
  similarity: number;
  location_type?: string;
  location_value?: string;
}

export interface Citation {
  source_id: string;
  filename: string;
  location_type: string;
  location_value: string;
  supported?: boolean;
}

export interface MessageBubbleProps {
  sender: 'user' | 'bot';
  content: string;
  timestamp?: string;
  sources?: Source[];
  citations?: Citation[];
  isLoading?: boolean;
}

export function MessageBubble({
  sender,
  content,
  timestamp,
  isLoading = false,
}: MessageBubbleProps) {
  const isUser = sender === 'user';

  return (
    <View style={[styles.wrapper, isUser ? styles.userWrapper : styles.botWrapper]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.botBubble]}>
        <Text style={[styles.text, isUser ? styles.userText : styles.botText]}>
          {isLoading ? '...' : content}
        </Text>
        {timestamp ? (
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
    paddingVertical: spacing.sm + 2,
    borderRadius: radii.lg,
    maxWidth: '85%',
  },
  userBubble: {
    backgroundColor: colors.ink,
    borderBottomRightRadius: 4,
  },
  botBubble: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
    borderBottomLeftRadius: 4,
  },
  text: {
    fontSize: fontSize.base,
    lineHeight: 20,
  },
  userText: {
    color: '#ffffff',
  },
  botText: {
    color: colors.ink,
  },
  time: {
    fontSize: fontSize.xs,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  userTime: {
    color: 'rgba(255, 255, 255, 0.6)',
  },
  botTime: {
    color: colors.muted,
  },
});
