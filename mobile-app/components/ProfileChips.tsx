import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface ProfileChipsProps {
  selected: 'fast' | 'quality';
  onChange: (profile: 'fast' | 'quality') => void;
}

export function ProfileChips({ selected, onChange }: ProfileChipsProps) {
  const isFast = selected === 'fast';
  const isQuality = selected === 'quality';

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.chip, isFast ? styles.activeChip : styles.inactiveChip]}
        onPress={() => onChange('fast')}
        activeOpacity={0.7}
        accessibilityRole="radio"
        accessibilityState={{ selected: isFast }}
        accessibilityLabel="Fast retrieval profile"
      >
        <Feather
          name="zap"
          size={14}
          color={isFast ? '#ffffff' : colors.chipInactiveText}
          style={styles.icon}
        />
        <Text style={[styles.chipText, isFast ? styles.activeChipText : styles.inactiveChipText]}>
          Fast
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.chip, isQuality ? styles.activeChip : styles.inactiveChip]}
        onPress={() => onChange('quality')}
        activeOpacity={0.7}
        accessibilityRole="radio"
        accessibilityState={{ selected: isQuality }}
        accessibilityLabel="Quality retrieval profile with BM25 and reranker"
      >
        <Feather
          name="star"
          size={14}
          color={isQuality ? '#ffffff' : colors.chipInactiveText}
          style={styles.icon}
        />
        <Text style={[styles.chipText, isQuality ? styles.activeChipText : styles.inactiveChipText]}>
          Quality
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xs,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radii.pill,
  },
  icon: {
    marginRight: 6,
  },
  activeChip: {
    backgroundColor: colors.chipActive,
  },
  inactiveChip: {
    backgroundColor: colors.chipInactive,
  },
  chipText: {
    fontSize: fontSize.sm,
    fontWeight: '600',
  },
  activeChipText: {
    color: '#ffffff',
  },
  inactiveChipText: {
    color: colors.chipInactiveText,
  },
});
