import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { colors, fontSize, radii, spacing } from '../lib/theme';

export interface CategorySheetProps {
  visible: boolean;
  categories: string[];
  selectedCategory: string;
  pickedFilename?: string;
  onSelect: (category: string) => void;
  onClose: () => void;
}

export function CategorySheet({
  visible,
  categories,
  selectedCategory,
  pickedFilename,
  onSelect,
  onClose,
}: CategorySheetProps) {
  const [newCategory, setNewCategory] = useState('');
  const [chosenCategory, setChosenCategory] = useState(selectedCategory || 'General');

  if (!visible) return null;

  // Filter out "All" from assignable upload categories
  const assignableCategories = Array.from(
    new Set(['General', ...categories.filter((c) => c && c.toLowerCase() !== 'all')])
  );

  const handleConfirm = () => {
    const finalCat = newCategory.trim() || chosenCategory || 'General';
    onSelect(finalCat);
    setNewCategory('');
  };

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
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.sheetWrapper}
        >
          <View
            style={styles.sheet}
            onStartShouldSetResponder={() => true}
          >
            <View style={styles.header}>
              <View>
                <Text style={styles.title}>Assign Category</Text>
                {pickedFilename ? (
                  <Text style={styles.filename} numberOfLines={1}>
                    File: {pickedFilename}
                  </Text>
                ) : null}
              </View>
              <TouchableOpacity
                onPress={onClose}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Feather name="x" size={20} color={colors.muted} />
              </TouchableOpacity>
            </View>

            <ScrollView style={[styles.list, { maxHeight: 220 }]}>
              {assignableCategories.map((cat) => {
                const isSelected = !newCategory.trim() && chosenCategory === cat;
                return (
                  <TouchableOpacity
                    key={cat}
                    style={[styles.option, isSelected && styles.selectedOption]}
                    onPress={() => {
                      setChosenCategory(cat);
                      setNewCategory('');
                    }}
                    activeOpacity={0.7}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        isSelected && styles.selectedOptionText,
                      ]}
                    >
                      {cat}
                    </Text>
                    {isSelected ? (
                      <Feather name="check" size={16} color={colors.ink} />
                    ) : null}
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            <View style={styles.newCategorySection}>
              <Text style={styles.sectionLabel}>Or enter a new category</Text>
              <View style={styles.newCategoryRow}>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. Finance, Legal, Engineering"
                  placeholderTextColor={colors.muted}
                  value={newCategory}
                  onChangeText={setNewCategory}
                  autoCapitalize="words"
                />
              </View>
            </View>

            <TouchableOpacity
              style={styles.confirmButton}
              onPress={handleConfirm}
              activeOpacity={0.8}
            >
              <Text style={styles.confirmButtonText}>Confirm & Upload</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </TouchableOpacity>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    justifyContent: 'flex-end',
  },
  sheetWrapper: {
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radii.lg,
    borderTopRightRadius: radii.lg,
    padding: spacing.xl,
    paddingBottom: spacing.xl + 16,
    maxHeight: '85%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  title: {
    fontSize: fontSize.lg,
    fontWeight: '700',
    color: colors.ink,
  },
  filename: {
    fontSize: fontSize.xs,
    color: colors.muted,
    marginTop: 2,
    maxWidth: 260,
  },
  list: {
    marginBottom: spacing.md,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
  newCategorySection: {
    marginTop: spacing.xs,
    marginBottom: spacing.lg,
  },
  sectionLabel: {
    fontSize: fontSize.xs,
    fontWeight: '600',
    color: colors.muted,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  newCategoryRow: {
    flexDirection: 'row',
    gap: spacing.sm,
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
  confirmButton: {
    height: 48,
    backgroundColor: colors.ink,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  confirmButtonText: {
    color: '#ffffff',
    fontSize: fontSize.base,
    fontWeight: '600',
  },
});
