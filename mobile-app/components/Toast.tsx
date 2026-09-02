import React, { useEffect, useRef } from 'react';
import {
  Animated,
  PanResponder,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { fontSize, radii, spacing } from '../lib/theme';

export interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'info';
  onDismiss?: () => void;
  duration?: number;
}

export function Toast({
  message,
  type = 'info',
  onDismiss,
  duration = 3000,
}: ToastProps) {
  const insets = useSafeAreaInsets();
  const topOffset = Math.max(insets.top + 8, 48);
  const translateY = useRef(new Animated.Value(-100)).current;

  const dismiss = () => {
    Animated.timing(translateY, {
      toValue: -120,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      onDismiss?.();
    });
  };

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, gestureState) => gestureState.dy < -5,
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dy < -15) {
          dismiss();
        }
      },
    })
  ).current;

  useEffect(() => {
    Animated.spring(translateY, {
      toValue: 0,
      useNativeDriver: true,
      bounciness: 4,
    }).start();

    const timer = setTimeout(() => {
      dismiss();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, translateY]);

  const bgStyle =
    type === 'success'
      ? styles.successBg
      : type === 'error'
      ? styles.errorBg
      : styles.infoBg;

  const textStyle =
    type === 'success'
      ? styles.successText
      : type === 'error'
      ? styles.errorText
      : styles.infoText;

  const iconName =
    type === 'success'
      ? 'check-circle'
      : type === 'error'
      ? 'alert-circle'
      : 'info';

  const iconColor =
    type === 'success'
      ? '#059669'
      : type === 'error'
      ? '#e11d48'
      : '#0284c7';

  return (
    <Animated.View
      style={[
        styles.container,
        { top: topOffset },
        bgStyle,
        { transform: [{ translateY }] },
      ]}
      accessibilityLiveRegion="polite"
      {...panResponder.panHandlers}
    >
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={dismiss}
        style={styles.touchable}
      >
        <Feather name={iconName} size={18} color={iconColor} style={styles.icon} />
        <Text style={[styles.text, textStyle]} numberOfLines={3}>
          {message}
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 50,
    left: spacing.lg,
    right: spacing.lg,
    zIndex: 9999,
    borderRadius: radii.md,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 8,
  },
  touchable: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
  },
  icon: {
    marginRight: spacing.sm,
  },
  text: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    flex: 1,
    lineHeight: 18,
  },
  successBg: {
    backgroundColor: '#dcfce7',
    borderColor: '#86efac',
  },
  successText: {
    color: '#059669',
  },
  errorBg: {
    backgroundColor: '#fee2e2',
    borderColor: '#fca5a5',
  },
  errorText: {
    color: '#e11d48',
  },
  infoBg: {
    backgroundColor: '#e0f2fe',
    borderColor: '#7dd3fc',
  },
  infoText: {
    color: '#0284c7',
  },
});
