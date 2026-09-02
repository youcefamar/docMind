import React, { useState } from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface CategorySheetProps {
  visible: boolean;
  categories: string[];
  selectedCategory: string;
  onSelect: (category: string) => void;
  onClose: () => void;
}

export function CategorySheet({
  visible,
  categories,
  selectedCategory,
  onSelect,
  onClose,
}: CategorySheetProps) {
  const [newCategory, setNewCategory] = useState('');

  if (!visible) return null;

  return (
    <Modal
      transparent
      visible={visible}
      animationType="slide"
      onRequestClose={onClose}
    >
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onClose}
      >
        <View
          style={styles.sheet}
          onStartShouldSetResponder={() => true}
        >
          <Text style={styles.title}>Select Category</Text>

          <ScrollView style={styles.list}>
            {categories.map((cat) => (
              <TouchableOpacity
                key={cat}
                style={[
                  styles.option,
                  selectedCategory === cat && styles.selectedOption,
                ]}
                onPress={() => {
                  onSelect(cat);
                  onClose();
                }}
              >
                <Text
                  style={[
                    styles.optionText,
                    selectedCategory === cat && styles.selectedOptionText,
                  ]}
                >
                  {cat}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <View style={styles.newCategoryRow}>
            <TextInput
              style={styles.input}
              placeholder="Or add new category..."
              placeholderTextColor={colors.muted}
              value={newCategory}
              onChangeText={setNewCategory}
            />
            <TouchableOpacity
              style={[
                styles.addButton,
                !newCategory.trim() && styles.addButtonDisabled,
              ]}
              disabled={!newCategory.trim()}
              onPress={() => {
                const trimmed = newCategory.trim();
                if (trimmed) {
                  onSelect(trimmed);
                  setNewCategory('');
                  onClose();
                }
              }}
            >
              <Text style={styles.addButtonText}>Use</Text>
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
    maxHeight: '70%',
  },
  title: {
    fontSize: fontSize.lg,
    fontWeight: '600',
    color: colors.ink,
    marginBottom: spacing.md,
  },
  list: {
    marginBottom: spacing.md,
  },
  option: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  selectedOption: {
    backgroundColor: colors.chipInactive,
    borderRadius: radii.sm,
  },
  optionText: {
    fontSize: fontSize.base,
    color: colors.ink,
  },
  selectedOptionText: {
    fontWeight: '600',
  },
  newCategoryRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  input: {
    flex: 1,
    height: 44,
    backgroundColor: colors.canvas,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: spacing.md,
    fontSize: fontSize.base,
    color: colors.ink,
  },
  addButton: {
    height: 44,
    paddingHorizontal: spacing.lg,
    backgroundColor: colors.ink,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addButtonDisabled: {
    opacity: 0.4,
  },
  addButtonText: {
    color: '#ffffff',
    fontSize: fontSize.base,
    fontWeight: '600',
  },
});
