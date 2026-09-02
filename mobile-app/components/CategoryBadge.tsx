import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { fontSize, radii } from '../lib/theme';

export interface CategoryBadgeProps {
  category: string;
}

const PALETTES = [
  { border: '#e2e8f0', bg: '#f8fafc', text: '#475569' },
  { border: '#bae6fd', bg: '#f0f9ff', text: '#0369a1' },
  { border: '#a7f3d0', bg: '#ecfdf5', text: '#047857' },
  { border: '#fde68a', bg: '#fffbeb', text: '#b45309' },
  { border: '#fecdd3', bg: '#fff1f2', text: '#be123c' },
];

export function CategoryBadge({ category }: CategoryBadgeProps) {
  const hash = Array.from(category || '').reduce(
    (sum, character) => sum + character.charCodeAt(0),
    0
  );
  const palette = PALETTES[hash % PALETTES.length];

  return (
    <View
      style={[
        styles.badge,
        {
          borderColor: palette.border,
          backgroundColor: palette.bg,
        },
      ]}
    >
      <Text style={[styles.text, { color: palette.text }]}>{category || 'General'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radii.sm,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: fontSize.xs,
    fontWeight: '500',
  },
});
