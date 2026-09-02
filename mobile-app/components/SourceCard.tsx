import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, radii, spacing } from '../lib/theme';
import { CategoryBadge } from './CategoryBadge';
import { Citation, Source } from './MessageBubble';

export interface SourceCardProps {
  sources: Source[];
  citations?: Citation[];
}

export function SourceCard({ sources }: SourceCardProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Sources ({sources.length})</Text>
      {sources.map((source, idx) => (
        <View key={`${source.doc_id}-${idx}`} style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.filename} numberOfLines={1}>
              {source.filename}
            </Text>
            <CategoryBadge category={source.category} />
          </View>
          <Text style={styles.excerpt} numberOfLines={2}>
            {source.excerpt}
          </Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: spacing.sm,
    gap: spacing.xs,
  },
  header: {
    fontSize: fontSize.xs,
    fontWeight: '600',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  card: {
    backgroundColor: '#fcfcfb',
    borderColor: '#e8e8e5',
    borderWidth: 1,
    borderRadius: radii.md,
    padding: spacing.sm,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  filename: {
    fontSize: fontSize.sm,
    fontWeight: '500',
    color: colors.ink,
    flex: 1,
    marginRight: spacing.sm,
  },
  excerpt: {
    fontSize: fontSize.xs,
    color: colors.muted,
    fontStyle: 'italic',
  },
});
