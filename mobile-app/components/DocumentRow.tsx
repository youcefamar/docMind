import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { colors, fontSize, radii, spacing } from '../lib/theme';
import { CategoryBadge } from './CategoryBadge';

export interface DocumentSummary {
  id: string;
  filename: string;
  category: string;
  chunk_count: number;
  total_pages: number;
  created_at: string;
  status: string;
  error_detail?: string | null;
}

export interface DocumentRowProps {
  doc: DocumentSummary;
  onDelete?: (id: string) => void;
}

export function DocumentRow({ doc, onDelete }: DocumentRowProps) {
  const isIndexed = doc.status === 'indexed';
  const isFailed = doc.status === 'failed';

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={styles.iconContainer}>
          <Feather name="file-text" size={20} color={colors.ink} />
        </View>

        <View style={styles.content}>
          <Text style={styles.filename} numberOfLines={1}>
            {doc.filename}
          </Text>

          <View style={styles.metaRow}>
            <CategoryBadge category={doc.category} />
            <Text style={styles.metaText}>
              {doc.total_pages > 0 ? `${doc.total_pages} pages · ` : ''}
              {doc.chunk_count} chunks
            </Text>
          </View>
        </View>

        <View style={styles.actions}>
          <View
            style={[
              styles.statusIndicator,
              isIndexed ? styles.indexed : isFailed ? styles.failed : styles.processing,
            ]}
          />
          {onDelete ? (
            <TouchableOpacity
              onPress={() => onDelete(doc.id)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Feather name="trash-2" size={16} color={colors.muted} />
            </TouchableOpacity>
          ) : null}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
    borderRadius: radii.md,
    marginHorizontal: spacing.lg,
    marginVertical: spacing.xs,
    padding: spacing.md,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: radii.sm,
    backgroundColor: colors.chipInactive,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
  },
  filename: {
    fontSize: fontSize.base,
    fontWeight: '500',
    color: colors.ink,
    marginBottom: 4,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  metaText: {
    fontSize: fontSize.xs,
    color: colors.muted,
  },
  actions: {
    alignItems: 'center',
    gap: spacing.sm,
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  indexed: {
    backgroundColor: colors.success,
  },
  failed: {
    backgroundColor: colors.error,
  },
  processing: {
    backgroundColor: colors.warning,
  },
});
