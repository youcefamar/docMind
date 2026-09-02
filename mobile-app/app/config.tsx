import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { getBaseUrl, saveBaseUrl, testConnection } from '../lib/api';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export default function ConfigScreen() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadSaved() {
      const saved = await getBaseUrl();
      if (saved) {
        setUrl(saved);
      }
    }
    loadSaved();
  }, []);

  const handleConnect = async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      setErrorMessage('Please enter a server URL.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const result = await testConnection(trimmed);
      if (result.success) {
        await saveBaseUrl(trimmed);
        router.replace('/(tabs)/chat');
      } else {
        setErrorMessage(result.error ?? 'Failed to connect to server.');
      }
    } catch {
      setErrorMessage('An unexpected error occurred while connecting.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      {router.canGoBack() ? (
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          accessibilityLabel="Go back"
        >
          <Feather name="arrow-left" size={22} color={colors.ink} />
        </TouchableOpacity>
      ) : null}
      <KeyboardAvoidingView
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.container}>
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <Feather name="cpu" size={28} color="#ffffff" />
            </View>
            <Text style={styles.title}>DocMind</Text>
            <Text style={styles.subtitle}>
              Connect to your local DocMind knowledge server
            </Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.inputLabel}>Server URL</Text>
            <View style={styles.inputWrapper}>
              <Feather name="server" size={18} color={colors.muted} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                value={url}
                onChangeText={(text) => {
                  setUrl(text);
                  if (errorMessage) setErrorMessage(null);
                }}
                placeholder="http://192.168.1.x:8000"
                placeholderTextColor={colors.muted}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="url"
                returnKeyType="done"
                onSubmitEditing={handleConnect}
                editable={!isLoading}
              />
            </View>

            {errorMessage ? (
              <View style={styles.errorBanner}>
                <Feather name="alert-circle" size={16} color={colors.error} />
                <Text style={styles.errorText}>{errorMessage}</Text>
              </View>
            ) : null}

            <TouchableOpacity
              style={[styles.connectButton, (isLoading || !url.trim()) && styles.connectButtonDisabled]}
              onPress={handleConnect}
              disabled={isLoading || !url.trim()}
              activeOpacity={0.8}
            >
              {isLoading ? (
                <View style={styles.buttonContent}>
                  <ActivityIndicator size="small" color="#ffffff" />
                  <Text style={styles.connectButtonText}>Connecting...</Text>
                </View>
              ) : (
                <View style={styles.buttonContent}>
                  <Text style={styles.connectButtonText}>Connect</Text>
                  <Feather name="arrow-right" size={18} color="#ffffff" />
                </View>
              )}
            </TouchableOpacity>

            <View style={styles.shortcutsRow}>
              <TouchableOpacity
                style={styles.shortcutChip}
                onPress={() => setUrl('http://localhost:8000')}
              >
                <Text style={styles.shortcutText}>localhost:8000</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.shortcutChip}
                onPress={() => setUrl('http://10.0.2.2:8000')}
              >
                <Text style={styles.shortcutText}>10.0.2.2:8000 (Android)</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.footer}>
            <Feather name="info" size={14} color={colors.muted} />
            <Text style={styles.footerText}>
              Your mobile device and DocMind server must be on the same local Wi-Fi network.
            </Text>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  keyboardAvoid: {
    flex: 1,
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  logoContainer: {
    width: 60,
    height: 60,
    borderRadius: radii.md,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.ink,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: fontSize.base,
    color: colors.muted,
    textAlign: 'center',
    maxWidth: 280,
    lineHeight: 20,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.line,
    padding: spacing.xl,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  inputLabel: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.ink,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.canvas,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: spacing.md,
    height: 48,
  },
  inputIcon: {
    marginRight: spacing.sm,
  },
  input: {
    flex: 1,
    height: '100%',
    fontSize: fontSize.base,
    color: colors.ink,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: '#fee2e2',
    borderColor: '#fca5a5',
    borderWidth: 1,
    borderRadius: radii.sm,
    padding: spacing.sm,
    marginTop: spacing.md,
  },
  errorText: {
    flex: 1,
    fontSize: fontSize.xs,
    color: colors.error,
    fontWeight: '500',
  },
  connectButton: {
    backgroundColor: colors.ink,
    borderRadius: radii.md,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.lg,
  },
  connectButtonDisabled: {
    opacity: 0.5,
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  connectButtonText: {
    fontSize: fontSize.base,
    fontWeight: '600',
    color: '#ffffff',
  },
  shortcutsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginTop: spacing.md,
  },
  shortcutChip: {
    backgroundColor: colors.chipInactive,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 4,
  },
  shortcutText: {
    fontSize: fontSize.xs,
    color: colors.chipInactiveText,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    marginTop: spacing.xl,
    paddingHorizontal: spacing.lg,
  },
  footerText: {
    fontSize: fontSize.xs,
    color: colors.muted,
    textAlign: 'center',
    lineHeight: 16,
    flex: 1,
  },
  backButton: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    alignSelf: 'flex-start',
  },
});
