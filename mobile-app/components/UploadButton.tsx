import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface UploadButtonProps {
  onPress: () => void;
  isLoading?: boolean;
  supportedExtensions?: string[];
}

export function UploadButton({
  onPress,
  isLoading = false,
  supportedExtensions = ['PDF', 'DOCX', 'PPTX', 'XLSX', 'TXT', 'MD'],
}: UploadButtonProps) {
  const extensionsText = supportedExtensions
    .map((ext) => ext.replace(/^\./, '').toUpperCase())
    .join(' · ');

  return (
    <TouchableOpacity
      style={[styles.button, isLoading && styles.buttonLoading]}
      onPress={onPress}
      disabled={isLoading}
      activeOpacity={0.7}
    >
      <View style={styles.content}>
        {isLoading ? (
          <ActivityIndicator size="small" color={colors.ink} style={styles.icon} />
        ) : (
          <Feather name="upload" size={18} color={colors.ink} style={styles.icon} />
        )}
        <Text style={styles.text}>
          {isLoading ? 'Uploading & extracting document...' : 'Pick files to upload'}
        </Text>
      </View>
      <Text style={styles.subtext}>{extensionsText}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.surface,
    borderColor: '#cbd5e1',
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderRadius: radii.md,
    marginHorizontal: spacing.lg,
    marginVertical: spacing.sm,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonLoading: {
    backgroundColor: colors.chipInactive,
    borderColor: colors.line,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    marginRight: spacing.sm,
  },
  text: {
    fontSize: fontSize.base,
    fontWeight: '600',
    color: colors.ink,
  },
  subtext: {
    fontSize: fontSize.xs,
    color: colors.muted,
    marginTop: 4,
    letterSpacing: 0.3,
  },
});
