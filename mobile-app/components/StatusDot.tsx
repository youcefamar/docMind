import React from 'react';
import { StyleSheet, View } from 'react-native';
import { colors } from '../lib/theme';

export interface StatusDotProps {
  ready: boolean;
  loading?: boolean;
  size?: number;
}

export function StatusDot({ ready, loading = false, size = 8 }: StatusDotProps) {
  const dotColor = loading ? colors.warning : ready ? colors.success : colors.error;

  return (
    <View
      style={[
        styles.dot,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          backgroundColor: dotColor,
        },
      ]}
      accessibilityRole="image"
      accessibilityLabel={loading ? 'Loading' : ready ? 'Ready' : 'Offline'}
    />
  );
}

const styles = StyleSheet.create({
  dot: {
    marginHorizontal: 4,
  },
});
