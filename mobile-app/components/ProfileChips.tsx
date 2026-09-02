import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface ProfileChipsProps {
  selected: 'fast' | 'quality';
  onChange: (profile: 'fast' | 'quality') => void;
}

export function ProfileChips({ selected, onChange }: ProfileChipsProps) {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[
          styles.chip,
          selected === 'fast' ? styles.activeChip : styles.inactiveChip,
        ]}
        onPress={() => onChange('fast')}
      >
        <Text
          style={[
            styles.chipText,
            selected === 'fast' ? styles.activeChipText : styles.inactiveChipText,
          ]}
        >
          Fast
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[
          styles.chip,
          selected === 'quality' ? styles.activeChip : styles.inactiveChip,
        ]}
        onPress={() => onChange('quality')}
      >
        <Text
          style={[
            styles.chipText,
            selected === 'quality' ? styles.activeChipText : styles.inactiveChipText,
          ]}
        >
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
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radii.pill,
  },
  activeChip: {
    backgroundColor: colors.chipActive,
  },
  inactiveChip: {
    backgroundColor: colors.chipInactive,
  },
  chipText: {
    fontSize: fontSize.sm,
    fontWeight: '500',
  },
  activeChipText: {
    color: '#ffffff',
  },
  inactiveChipText: {
    color: colors.chipInactiveText,
  },
});
