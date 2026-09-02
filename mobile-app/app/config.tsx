import { StyleSheet, Text, View } from 'react-native';
import { colors, fontSize } from '../lib/theme';

export default function ConfigScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Server Configuration</Text>
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
  title: {
    fontSize: fontSize.xl,
    fontWeight: '600',
    color: colors.ink,
  },
});
