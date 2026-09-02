import React, { useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Swipeable } from 'react-native-gesture-handler';
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
  onDelete: (doc: DocumentSummary) => void;
  onReindex?: (doc: DocumentSummary) => void;
}

function formatDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}

export function DocumentRow({ doc, onDelete, onReindex }: DocumentRowProps) {
  const [isErrorExpanded, setIsErrorExpanded] = useState(false);

  const isIndexed = doc.status === 'indexed';
  const isFailed = doc.status === 'failed';
  const isProcessing = doc.status === 'processing' || doc.status === 'queued';

  const renderRightActions = () => (
    <TouchableOpacity
      style={styles.deleteSwipeAction}
      onPress={() => onDelete(doc)}
      activeOpacity={0.8}
    >
      <Feather name="trash-2" size={20} color="#ffffff" />
      <Text style={styles.deleteSwipeText}>Delete</Text>
    </TouchableOpacity>
  );

  return (
    <Swipeable
      renderRightActions={renderRightActions}
      overshootRight={false}
      containerStyle={styles.swipeableContainer}
    >
      <TouchableOpacity
        style={[styles.card, isFailed && styles.cardFailed]}
        activeOpacity={isFailed ? 0.7 : 1}
        onPress={() => {
          if (isFailed) {
            setIsErrorExpanded((prev) => !prev);
          }
        }}
      >
        <View style={styles.row}>
          <View style={[styles.iconContainer, isFailed && styles.iconContainerFailed]}>
            <Feather
              name="file-text"
              size={20}
              color={isFailed ? colors.error : colors.ink}
            />
          </View>

          <View style={styles.content}>
            <View style={styles.titleRow}>
              <Text style={styles.filename} numberOfLines={1}>
                {doc.filename}
              </Text>
              {isIndexed ? (
                <Feather name="check-circle" size={16} color={colors.success} />
              ) : isFailed ? (
                <Feather name="alert-circle" size={16} color={colors.error} />
              ) : isProcessing ? (
                <ActivityIndicator size="small" color={colors.warning} />
              ) : null}
            </View>

            <View style={styles.metaRow}>
              <CategoryBadge category={doc.category} />
              <Text style={styles.metaText}>
                {doc.total_pages > 0 ? `${doc.total_pages} pages · ` : ''}
                {doc.chunk_count} chunks
              </Text>
              {doc.created_at ? (
                <Text style={styles.dateText}>· {formatDate(doc.created_at)}</Text>
              ) : null}
            </View>
          </View>

          <TouchableOpacity
            style={styles.trashIconButton}
            onPress={() => onDelete(doc)}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            accessibilityLabel={`Delete ${doc.filename}`}
          >
            <Feather name="trash-2" size={16} color={colors.muted} />
          </TouchableOpacity>
        </View>

        {isFailed && isErrorExpanded && doc.error_detail ? (
          <View style={styles.errorContainer}>
            <Text style={styles.errorDetailText}>{doc.error_detail}</Text>
            {onReindex ? (
              <TouchableOpacity
                style={styles.reindexButton}
                onPress={() => onReindex(doc)}
              >
                <Feather name="refresh-cw" size={12} color={colors.ink} />
                <Text style={styles.reindexText}>Retry indexing</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        ) : isFailed && !isErrorExpanded ? (
          <Text style={styles.tapToViewError}>Tap to view error detail</Text>
        ) : null}
      </TouchableOpacity>
    </Swipeable>
  );
}

const styles = StyleSheet.create({
  swipeableContainer: {
    marginHorizontal: spacing.lg,
    marginVertical: spacing.xs,
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
    borderRadius: radii.md,
    padding: spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  cardFailed: {
    borderColor: '#fca5a5',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: radii.sm,
    backgroundColor: colors.chipInactive,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainerFailed: {
    backgroundColor: '#fee2e2',
  },
  content: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
    gap: spacing.xs,
  },
  filename: {
    fontSize: fontSize.base,
    fontWeight: '600',
    color: colors.ink,
    flex: 1,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    flexWrap: 'wrap',
  },
  metaText: {
    fontSize: fontSize.xs,
    color: colors.muted,
  },
  dateText: {
    fontSize: fontSize.xs,
    color: colors.muted,
  },
  trashIconButton: {
    padding: 6,
  },
  deleteSwipeAction: {
    backgroundColor: colors.error,
    justifyContent: 'center',
    alignItems: 'center',
    width: 80,
    borderRadius: radii.md,
    marginLeft: spacing.xs,
  },
  deleteSwipeText: {
    color: '#ffffff',
    fontSize: fontSize.xs,
    fontWeight: '600',
    marginTop: 2,
  },
  errorContainer: {
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#fecdd3',
  },
  errorDetailText: {
    fontSize: fontSize.xs,
    color: colors.error,
    lineHeight: 16,
  },
  reindexButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: spacing.xs,
    alignSelf: 'flex-start',
    backgroundColor: colors.chipInactive,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: radii.sm,
  },
  reindexText: {
    fontSize: fontSize.xs,
    fontWeight: '600',
    color: colors.ink,
  },
  tapToViewError: {
    fontSize: fontSize.xs,
    color: colors.error,
    marginTop: 4,
    fontStyle: 'italic',
  },
});
