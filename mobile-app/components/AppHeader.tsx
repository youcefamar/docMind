import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, spacing } from '../lib/theme';

export interface AppHeaderProps {
  title: string;
  subtitle?: string;
  leftAction?: React.ReactNode;
  rightActions?: React.ReactNode;
  showBorder?: boolean;
}

export function AppHeader({
  title,
  subtitle,
  leftAction,
  rightActions,
  showBorder = true,
}: AppHeaderProps) {
  return (
    <View style={[styles.header, !showBorder && styles.noBorder]}>
      <View style={styles.leftContainer}>
        {leftAction ? <View style={styles.leftAction}>{leftAction}</View> : null}
        <View>
          <Text style={styles.title}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
      </View>
      {rightActions ? <View style={styles.rightActions}>{rightActions}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
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
  noBorder: {
    borderBottomWidth: 0,
  },
  leftContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  leftAction: {
    marginRight: 4,
  },
  title: {
    fontSize: fontSize.xl,
    fontWeight: '700',
    color: colors.ink,
  },
  subtitle: {
    fontSize: fontSize.xs,
    color: colors.muted,
  },
  rightActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
});
