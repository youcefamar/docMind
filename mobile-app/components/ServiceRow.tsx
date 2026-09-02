import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, radii, spacing } from '../lib/theme';
import { StatusDot } from './StatusDot';

export interface ServiceRowProps {
  label: string;
  ready: boolean;
  loading?: boolean;
  statusText?: string;
  isLast?: boolean;
  icon?: React.ReactNode;
}

export function ServiceRow({
  label,
  ready,
  loading = false,
  statusText,
  isLast = false,
  icon,
}: ServiceRowProps) {
  const displayStatus =
    statusText || (loading ? 'Loading' : ready ? 'Ready' : 'Not Ready');

  return (
    <View style={[styles.row, isLast && styles.rowLast]}>
      <View style={styles.left}>
        {icon ? (
          icon
        ) : (
          <StatusDot ready={ready} loading={loading} />
        )}
        <Text style={styles.label}>{label}</Text>
      </View>
      <View
        style={[
          styles.badge,
          loading
            ? styles.loadingBadge
            : ready
            ? styles.readyBadge
            : styles.errorBadge,
        ]}
      >
        <Text
          style={[
            styles.badgeText,
            loading
              ? styles.loadingText
              : ready
              ? styles.readyText
              : styles.errorText,
          ]}
        >
          {displayStatus}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  rowLast: {
    borderBottomWidth: 0,
    paddingBottom: 0,
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  label: {
    fontSize: fontSize.base,
    color: '#31363b',
    fontWeight: '500',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radii.sm,
  },
  badgeText: {
    fontSize: fontSize.xs,
    fontWeight: '600',
  },
  readyBadge: {
    backgroundColor: '#ecfdf5',
  },
  readyText: {
    color: colors.success,
    fontSize: fontSize.xs,
    fontWeight: '600',
  },
  loadingBadge: {
    backgroundColor: '#fffbeb',
  },
  loadingText: {
    color: colors.warning,
    fontSize: fontSize.xs,
    fontWeight: '600',
  },
  errorBadge: {
    backgroundColor: '#fee2e2',
  },
  errorText: {
    color: colors.error,
    fontSize: fontSize.xs,
    fontWeight: '600',
  },
});
