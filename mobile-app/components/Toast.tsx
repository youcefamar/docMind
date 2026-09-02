import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text, TouchableOpacity } from 'react-native';
import { fontSize, radii, spacing } from '../lib/theme';

export interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'info';
  onDismiss?: () => void;
  duration?: number;
}

export function Toast({ message, type = 'info', onDismiss, duration = 3000 }: ToastProps) {
  const translateY = useRef(new Animated.Value(-100)).current;

  useEffect(() => {
    Animated.spring(translateY, {
      toValue: 0,
      useNativeDriver: true,
      bounciness: 4,
    }).start();

    const timer = setTimeout(() => {
      Animated.timing(translateY, {
        toValue: -100,
        duration: 250,
        useNativeDriver: true,
      }).start(() => {
        onDismiss?.();
      });
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onDismiss, translateY]);

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

  return (
    <Animated.View
      style={[styles.container, bgStyle, { transform: [{ translateY }] }]}
      accessibilityLiveRegion="polite"
    >
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => {
          Animated.timing(translateY, {
            toValue: -100,
            duration: 200,
            useNativeDriver: true,
          }).start(() => {
            onDismiss?.();
          });
        }}
        style={styles.touchable}
      >
        <Text style={[styles.text, textStyle]}>{message}</Text>
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
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 6,
  },
  touchable: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  text: {
    fontSize: fontSize.md,
    fontWeight: '500',
    textAlign: 'center',
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
