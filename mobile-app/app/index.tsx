import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { getBaseUrl, testConnection } from '../lib/api';
import { colors } from '../lib/theme';

export default function Index() {
  useEffect(() => {
    let isMounted = true;

    async function checkConfiguration() {
      const base = await getBaseUrl();
      if (!isMounted) return;

      if (!base) {
        router.replace('/config');
        return;
      }

      try {
        const result = await testConnection(base);
        if (!isMounted) return;

        if (result.success) {
          router.replace('/(tabs)/chat');
        } else {
          router.replace('/config');
        }
      } catch {
        if (isMounted) {
          router.replace('/config');
        }
      }
    }

    checkConfiguration();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color={colors.ink} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.canvas,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
