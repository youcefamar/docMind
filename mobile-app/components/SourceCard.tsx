import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { colors, fontSize, radii, spacing } from '../lib/theme';
import { CategoryBadge } from './CategoryBadge';

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

export interface SourceCardProps {
  sources: Source[];
  citations?: Citation[];
}

function sourceKey(source: Source, index: number) {
  return `${source.doc_id}-${source.page_number}-${index}`;
}

export function SourceCard({ sources, citations = [] }: SourceCardProps) {
  const [expandedKey, setExpandedKey] = useState<string | null>(() =>
    sources.length > 0 ? sourceKey(sources[0], 0) : null
  );

  if (!sources || sources.length === 0) return null;

  const toggleExpand = (key: string) => {
    setExpandedKey((current) => (current === key ? null : key));
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Feather name="shield" size={13} color={colors.muted} />
        <Text style={styles.headerTitle}>Verified Sources ({sources.length})</Text>
      </View>

      {citations.length > 0 ? (
        <View style={styles.citationsContainer}>
          {citations.map((cit) => (
            <View
              key={cit.source_id}
              style={[
                styles.citationBadge,
                cit.supported ? styles.citationSupported : styles.citationReview,
              ]}
            >
              <Text
                style={[
                  styles.citationText,
                  cit.supported
                    ? styles.citationTextSupported
                    : styles.citationTextReview,
                ]}
              >
                {cit.source_id} · {cit.supported ? 'supported' : 'needs review'}
              </Text>
            </View>
          ))}
        </View>
      ) : null}

      <View style={styles.cardsList}>
        {sources.map((source, index) => {
          const key = sourceKey(source, index);
          const isExpanded = expandedKey === key;
          const matchPercent = Math.round(source.similarity * 100);

          return (
            <TouchableOpacity
              key={key}
              style={[styles.card, isExpanded && styles.cardExpanded]}
              activeOpacity={0.7}
              onPress={() => toggleExpand(key)}
            >
              <View style={styles.cardHeader}>
                <View style={styles.cardTitleArea}>
                  <Feather name="file-text" size={14} color={colors.ink} style={styles.fileIcon} />
                  <Text style={styles.filename} numberOfLines={1}>
                    {source.filename}
                  </Text>
                </View>

                <View style={styles.cardHeaderRight}>
                  <CategoryBadge category={source.category} />
                  <Feather
                    name={isExpanded ? 'chevron-up' : 'chevron-down'}
                    size={16}
                    color={colors.muted}
                  />
                </View>
              </View>

              <View style={styles.metaRow}>
                <Text style={styles.metaText}>
                  Page {source.page_number}
                  {source.total_pages > 0 ? ` of ${source.total_pages}` : ''}
                </Text>
                {matchPercent > 0 ? (
                  <Text style={styles.scoreText}>{matchPercent}% match</Text>
                ) : null}
              </View>

              {isExpanded && source.excerpt ? (
                <View style={styles.excerptContainer}>
                  <Text style={styles.excerptText}>"{source.excerpt.trim()}"</Text>
                </View>
              ) : null}
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: spacing.md,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: spacing.xs,
  },
  headerTitle: {
    fontSize: fontSize.xs,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  citationsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: spacing.sm,
  },
  citationBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radii.pill,
    borderWidth: 1,
  },
  citationSupported: {
    backgroundColor: '#ecfdf5',
    borderColor: '#a7f3d0',
  },
  citationReview: {
    backgroundColor: '#fffbeb',
    borderColor: '#fde68a',
  },
  citationText: {
    fontSize: fontSize.xs,
    fontWeight: '600',
  },
  citationTextSupported: {
    color: '#047857',
  },
  citationTextReview: {
    color: '#b45309',
  },
  cardsList: {
    gap: spacing.xs,
  },
  card: {
    backgroundColor: '#fcfcfb',
    borderColor: '#e8e8e5',
    borderWidth: 1,
    borderRadius: radii.md,
    padding: spacing.sm + 2,
  },
  cardExpanded: {
    backgroundColor: '#ffffff',
    borderColor: '#d0d4d9',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: spacing.xs,
  },
  cardTitleArea: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: spacing.xs,
  },
  fileIcon: {
    marginRight: 6,
  },
  filename: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.ink,
    flex: 1,
  },
  cardHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  metaText: {
    fontSize: fontSize.xs,
    color: colors.muted,
  },
  scoreText: {
    fontSize: fontSize.xs,
    fontWeight: '600',
    color: colors.muted,
  },
  excerptContainer: {
    marginTop: spacing.sm,
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: '#f1f3f4',
  },
  excerptText: {
    fontSize: fontSize.xs,
    color: '#475569',
    lineHeight: 18,
    fontStyle: 'italic',
  },
});
