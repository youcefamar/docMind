import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import { apiFetch, getApiErrorMessage, readApiPayload } from '../../lib/api';
import { colors, fontSize, radii, spacing } from '../../lib/theme';
import { CategorySheet } from '../../components/CategorySheet';
import { ConfirmSheet } from '../../components/ConfirmSheet';
import { DocumentRow, DocumentSummary } from '../../components/DocumentRow';
import { EmptyState } from '../../components/EmptyState';
import { Toast } from '../../components/Toast';
import { UploadButton } from '../../components/UploadButton';

interface PublicConfig {
  categories?: string[];
  supported_extensions?: string[];
  default_category?: string;
}

interface PickedFileInfo {
  uri: string;
  name: string;
  mimeType?: string;
  size?: number;
}

export default function DocumentsScreen() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [supportedExtensions, setSupportedExtensions] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Modals & Popups
  const [pickedFile, setPickedFile] = useState<PickedFileInfo | null>(null);
  const [isCategorySheetVisible, setIsCategorySheetVisible] = useState(false);
  const [deleteTargetDoc, setDeleteTargetDoc] = useState<DocumentSummary | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(
    null
  );

  const showToast = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ text, type });
  };

  // Load backend config (categories, supported types)
  const fetchConfig = useCallback(async () => {
    try {
      const res = await apiFetch('/api/config/');
      if (res.ok) {
        const data = await readApiPayload<PublicConfig>(res);
        if (data) {
          setCategories(data.categories || []);
          setSupportedExtensions(data.supported_extensions || []);
        }
      }
    } catch {
      // Ignore config load error
    }
  }, []);

  // Load document list
  const fetchDocuments = useCallback(async (): Promise<DocumentSummary[]> => {
    try {
      const res = await apiFetch('/api/docs');
      if (res.ok) {
        const data = await readApiPayload<unknown>(res);
        if (Array.isArray(data)) {
          const list = data as DocumentSummary[];
          setDocuments(list);
          return list;
        }
      }
    } catch (err) {
      console.warn('Failed to fetch documents:', err);
    }
    return [];
  }, []);

  const refreshDocumentsUntilSettled = useCallback(async () => {
    const list = await fetchDocuments();
    if (list.some((d) => d.status === 'processing' || d.status === 'queued')) {
      setTimeout(refreshDocumentsUntilSettled, 1500);
    }
  }, [fetchDocuments]);

  useEffect(() => {
    async function init() {
      setIsLoading(true);
      await Promise.allSettled([fetchConfig(), fetchDocuments()]);
      setIsLoading(false);
    }
    init();
  }, [fetchConfig, fetchDocuments]);

  // Pull to refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.allSettled([fetchConfig(), fetchDocuments()]);
    setIsRefreshing(false);
  };

  // Knowledge folder background sync
  const handleSyncSources = async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    try {
      const res = await apiFetch('/api/sources/sync', { method: 'POST' });
      if (res.ok) {
        showToast('Knowledge folder sync queued in background.', 'success');
        refreshDocumentsUntilSettled();
      } else {
        const payload = await readApiPayload(res);
        showToast(getApiErrorMessage(payload, 'Failed to trigger folder sync.'), 'error');
      }
    } catch {
      showToast('Could not reach server to start folder sync.', 'error');
    } finally {
      setIsSyncing(false);
    }
  };

  // Pick file to upload
  const handlePickFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true,
      });

      if (result.canceled || !result.assets || result.assets.length === 0) {
        return;
      }

      const asset = result.assets[0];
      setPickedFile({
        uri: asset.uri,
        name: asset.name,
        mimeType: asset.mimeType ?? undefined,
        size: asset.size,
      });
      setIsCategorySheetVisible(true);
    } catch (err) {
      console.warn('Error picking document:', err);
      showToast('Failed to select file.', 'error');
    }
  };

  // Upload file with chosen category
  const handleConfirmUpload = async (category: string) => {
    if (!pickedFile) return;

    setIsCategorySheetVisible(false);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('files', {
        uri: pickedFile.uri,
        name: pickedFile.name,
        type: pickedFile.mimeType || 'application/octet-stream',
      } as unknown as Blob);
      formData.append('category', category);

      const res = await apiFetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errorPayload = await readApiPayload(res);
        throw new Error(getApiErrorMessage(errorPayload, `Upload failed (HTTP ${res.status})`));
      }

      showToast(`'${pickedFile.name}' uploaded and indexed successfully!`, 'success');
      setPickedFile(null);
      refreshDocumentsUntilSettled();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to upload document.';
      showToast(msg, 'error');
    } finally {
      setIsUploading(false);
    }
  };

  // Delete document
  const handleConfirmDelete = async () => {
    if (!deleteTargetDoc) return;
    const docId = deleteTargetDoc.id;
    const filename = deleteTargetDoc.filename;
    setDeleteTargetDoc(null);

    try {
      const res = await apiFetch(`/api/doc/${docId}`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        const payload = await readApiPayload(res);
        throw new Error(getApiErrorMessage(payload, 'Failed to delete document.'));
      }

      showToast(`'${filename}' deleted.`, 'success');
      await fetchDocuments();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Could not delete document.';
      showToast(msg, 'error');
    }
  };

  // Reindex single failed document
  const handleReindex = async (doc: DocumentSummary) => {
    try {
      const res = await apiFetch(`/api/doc/${doc.id}/reindex`, {
        method: 'POST',
      });
      if (res.ok) {
        showToast(`Reindexing '${doc.filename}'...`, 'info');
        refreshDocumentsUntilSettled();
      } else {
        const payload = await readApiPayload(res);
        showToast(getApiErrorMessage(payload, 'Reindex failed.'), 'error');
      }
    } catch {
      showToast('Network error while requesting reindex.', 'error');
    }
  };

  // Filtered documents list
  const filteredDocuments = useMemo(() => {
    let list = [...documents];

    if (selectedCategory && selectedCategory !== 'All') {
      list = list.filter(
        (d) => (d.category || 'General').toLowerCase() === selectedCategory.toLowerCase()
      );
    }

    if (searchTerm.trim()) {
      const term = searchTerm.trim().toLowerCase();
      list = list.filter(
        (d) =>
          d.filename.toLowerCase().includes(term) ||
          d.category.toLowerCase().includes(term)
      );
    }

    return list;
  }, [documents, selectedCategory, searchTerm]);

  const allCategoryChips = ['All', ...categories];

  return (
    <SafeAreaView style={styles.safeArea}>
      {toast ? (
        <Toast
          message={toast.text}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      ) : null}

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Documents</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.syncButton}
            onPress={handleSyncSources}
            disabled={isSyncing}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            accessibilityLabel="Sync knowledge folder"
          >
            {isSyncing ? (
              <ActivityIndicator size="small" color={colors.ink} />
            ) : (
              <Feather name="refresh-cw" size={18} color={colors.ink} />
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Input */}
      <View style={styles.searchBarContainer}>
        <View style={styles.searchWrapper}>
          <Feather name="search" size={16} color={colors.muted} style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search documents by name or category..."
            placeholderTextColor={colors.muted}
            value={searchTerm}
            onChangeText={setSearchTerm}
            autoCapitalize="none"
            clearButtonMode="while-editing"
          />
          {searchTerm ? (
            <TouchableOpacity onPress={() => setSearchTerm('')}>
              <Feather name="x-circle" size={16} color={colors.muted} />
            </TouchableOpacity>
          ) : null}
        </View>
      </View>

      {/* Category Filter Chips */}
      {allCategoryChips.length > 1 ? (
        <View style={styles.categoryFilterContainer}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoryFilterScroll}
          >
            {allCategoryChips.map((cat) => {
              const isSelected = selectedCategory === cat;
              return (
                <TouchableOpacity
                  key={cat}
                  style={[
                    styles.filterChip,
                    isSelected ? styles.filterChipActive : styles.filterChipInactive,
                  ]}
                  onPress={() => setSelectedCategory(cat)}
                  activeOpacity={0.7}
                >
                  <Text
                    style={[
                      styles.filterChipText,
                      isSelected
                        ? styles.filterChipTextActive
                        : styles.filterChipTextInactive,
                    ]}
                  >
                    {cat}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      ) : null}

      {/* Document List */}
      <FlatList
        data={filteredDocuments}
        keyExtractor={(item) => item.id}
        keyboardDismissMode="on-drag"
        keyboardShouldPersistTaps="handled"
        renderItem={({ item }) => (
          <DocumentRow
            doc={item}
            onDelete={(doc) => setDeleteTargetDoc(doc)}
            onReindex={handleReindex}
          />
        )}
        ListHeaderComponent={
          <UploadButton
            onPress={handlePickFile}
            isLoading={isUploading}
            supportedExtensions={supportedExtensions}
          />
        }
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.ink} />
              <Text style={styles.loadingText}>Loading documents...</Text>
            </View>
          ) : (
            <EmptyState
              icon={<Feather name="file-text" size={40} color={colors.muted} />}
              title={
                searchTerm || (selectedCategory && selectedCategory !== 'All')
                  ? 'No matching documents'
                  : 'No documents yet'
              }
              subtitle={
                searchTerm || (selectedCategory && selectedCategory !== 'All')
                  ? 'Try searching with a different term or clearing your category filter.'
                  : 'Upload your first PDF, DOCX, or text document to start querying your knowledge base.'
              }
            />
          )
        }
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={colors.ink}
          />
        }
      />

      {/* Category Selection Sheet before upload */}
      <CategorySheet
        visible={isCategorySheetVisible}
        categories={categories}
        selectedCategory={selectedCategory === 'All' ? 'General' : selectedCategory}
        pickedFilename={pickedFile?.name}
        onSelect={handleConfirmUpload}
        onClose={() => {
          setIsCategorySheetVisible(false);
          setPickedFile(null);
        }}
      />

      {/* Delete Confirmation Sheet */}
      <ConfirmSheet
        visible={deleteTargetDoc !== null}
        title="Delete document?"
        message={`Are you sure you want to delete '${deleteTargetDoc?.filename}'? Extracted chunks and indexes will be permanently removed.`}
        confirmText="Delete Document"
        isDestructive={true}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTargetDoc(null)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  header: {
    height: 56,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
  },
  headerTitle: {
    fontSize: fontSize.xl,
    fontWeight: '700',
    color: colors.ink,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  syncButton: {
    padding: 6,
  },
  searchBarContainer: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  searchWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.canvas,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: spacing.md,
    height: 40,
  },
  searchIcon: {
    marginRight: spacing.sm,
  },
  searchInput: {
    flex: 1,
    height: '100%',
    fontSize: fontSize.base,
    color: colors.ink,
  },
  categoryFilterContainer: {
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    paddingBottom: spacing.sm,
  },
  categoryFilterScroll: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    gap: spacing.xs,
  },
  filterChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 5,
    borderRadius: radii.pill,
  },
  filterChipActive: {
    backgroundColor: colors.chipActive,
  },
  filterChipInactive: {
    backgroundColor: colors.chipInactive,
  },
  filterChipText: {
    fontSize: fontSize.xs,
    fontWeight: '600',
  },
  filterChipTextActive: {
    color: '#ffffff',
  },
  filterChipTextInactive: {
    color: colors.chipInactiveText,
  },
  listContent: {
    paddingBottom: spacing.xl,
    flexGrow: 1,
  },
  loadingContainer: {
    padding: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  loadingText: {
    fontSize: fontSize.sm,
    color: colors.muted,
  },
});
