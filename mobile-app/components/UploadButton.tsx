import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface UploadButtonProps {
  onPress: () => void;
  isLoading?: boolean;
}

export function UploadButton({ onPress, isLoading = false }: UploadButtonProps) {
  return (
    <TouchableOpacity
      style={styles.button}
      onPress={onPress}
      disabled={isLoading}
      activeOpacity={0.8}
    >
      <View style={styles.content}>
        <Feather name="upload" size={18} color={colors.ink} />
        <Text style={styles.text}>
          {isLoading ? 'Uploading...' : 'Pick files to upload'}
        </Text>
      </View>
      <Text style={styles.subtext}>PDF · DOCX · PPTX · XLSX · TXT · MD</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
    borderRadius: radii.md,
    marginHorizontal: spacing.lg,
    marginVertical: spacing.sm,
    padding: spacing.md,
    alignItems: 'center',
    borderStyle: 'dashed',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  text: {
    fontSize: fontSize.base,
    fontWeight: '500',
    color: colors.ink,
  },
  subtext: {
    fontSize: fontSize.xs,
    color: colors.muted,
    marginTop: 4,
  },
});
