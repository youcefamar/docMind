import React from 'react';
import { Modal, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface ConfirmSheetProps {
  visible: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmSheet({
  visible,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDestructive = true,
  onConfirm,
  onCancel,
}: ConfirmSheetProps) {
  const insets = useSafeAreaInsets();
  if (!visible) return null;

  return (
    <Modal
      transparent
      visible={visible}
      animationType="fade"
      onRequestClose={onCancel}
    >
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onCancel}
      >
        <View
          style={[
            styles.sheet,
            { paddingBottom: Math.max(insets.bottom, 12) + spacing.lg },
          ]}
          onStartShouldSetResponder={() => true}
        >
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.message}>{message}</Text>

          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onCancel}
            >
              <Text style={styles.cancelText}>{cancelText}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.button,
                isDestructive ? styles.destructiveButton : styles.primaryButton,
              ]}
              onPress={onConfirm}
            >
              <Text
                style={[
                  styles.confirmText,
                  isDestructive ? styles.destructiveText : styles.primaryText,
                ]}
              >
                {confirmText}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radii.lg,
    borderTopRightRadius: radii.lg,
    padding: spacing.xl,
    paddingBottom: spacing.xl + 12,
  },
  title: {
    fontSize: fontSize.lg,
    fontWeight: '600',
    color: colors.ink,
    marginBottom: spacing.xs,
  },
  message: {
    fontSize: fontSize.base,
    color: colors.muted,
    lineHeight: 20,
    marginBottom: spacing.xl,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  button: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    backgroundColor: colors.chipInactive,
  },
  cancelText: {
    fontSize: fontSize.base,
    fontWeight: '500',
    color: colors.ink,
  },
  primaryButton: {
    backgroundColor: colors.ink,
  },
  primaryText: {
    color: '#ffffff',
  },
  destructiveButton: {
    backgroundColor: '#fee2e2',
  },
  destructiveText: {
    color: colors.error,
  },
  confirmText: {
    fontSize: fontSize.base,
    fontWeight: '600',
  },
});
