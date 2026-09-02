import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import { apiFetch, getBaseUrl, readApiPayload } from '../../lib/api';
import { colors, fontSize, radii, spacing } from '../../lib/theme';
import { ServiceRow } from '../../components/ServiceRow';

interface RuntimeStatus {
  embedding_ready: boolean;
  dense_index_ready: boolean;
  bm25_index_ready: boolean;
  reranker_ready: boolean;
  quality_ready: boolean;
  llm_ready: boolean;
  llm_backend: string;
  llm_model: string;
  document_count: number;
  indexed_document_count: number;
  indexing_queue?: {
    size: number;
    active: boolean;
  };
}

interface SourceStatus {
  status: string;
  source_dir: string;
  discovered: number;
  indexed: number;
  unchanged: number;
  removed: number;
  failed: number;
  queued?: number;
  last_sync_at?: string | null;
}

const STATUS_POLL_INTERVAL_MS = 10000;

export default function StatusScreen() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null);
  const [sourceStatus, setSourceStatus] = useState<SourceStatus | null>(null);
  const [serverUrl, setServerUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchStatus = useCallback(async (isManual = false) => {
    if (isManual) setIsRefreshing(true);

    try {
      const url = await getBaseUrl();
      setServerUrl(url);

      const [runtimeRes, sourceRes] = await Promise.allSettled([
        apiFetch('/api/runtime/status'),
        apiFetch('/api/sources/status'),
      ]);

      let hasSuccess = false;

      if (runtimeRes.status === 'fulfilled' && runtimeRes.value.ok) {
        const runtimeData = await readApiPayload<RuntimeStatus>(runtimeRes.value);
        if (runtimeData) {
          setStatus(runtimeData);
          hasSuccess = true;
        }
      }

      if (sourceRes.status === 'fulfilled' && sourceRes.value.ok) {
        const sourceData = await readApiPayload<SourceStatus>(sourceRes.value);
        if (sourceData) {
          setSourceStatus(sourceData);
        }
      }

      if (hasSuccess) {
        setLastUpdated(new Date());
        setErrorMessage(null);
      } else {
        setErrorMessage('Could not load status from server.');
      }
    } catch {
      setErrorMessage('Server connection lost. Please verify connection.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Poll status every 10s while screen is in focus
  useFocusEffect(
    useCallback(() => {
      fetchStatus();
      const interval = setInterval(() => {
        fetchStatus();
      }, STATUS_POLL_INTERVAL_MS);

      return () => clearInterval(interval);
    }, [fetchStatus])
  );

  const formatTime = (date: Date | null) => {
    if (!date) return 'Never';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const queueSize = status?.indexing_queue?.size ?? 0;
  const isQueueActive = status?.indexing_queue?.active ?? false;

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>System Status</Text>
        <TouchableOpacity
          style={styles.headerButton}
          onPress={() => fetchStatus(true)}
          disabled={isRefreshing}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          accessibilityLabel="Refresh status"
        >
          {isRefreshing ? (
            <ActivityIndicator size="small" color={colors.ink} />
          ) : (
            <Feather name="refresh-cw" size={18} color={colors.ink} />
          )}
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => fetchStatus(true)}
            tintColor={colors.ink}
          />
        }
      >
        {errorMessage ? (
          <View style={styles.errorCard}>
            <Feather name="alert-circle" size={16} color={colors.error} />
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        ) : null}

        {/* Runtime Services Section */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Feather name="activity" size={16} color={colors.ink} />
            <Text style={styles.cardTitle}>Runtime Services</Text>
          </View>

          <ServiceRow
            label="Embedding model (Qwen 0.6B)"
            ready={Boolean(status?.embedding_ready)}
            loading={isLoading && !status}
          />
          <ServiceRow
            label="Dense index (FAISS Flat IP)"
            ready={Boolean(status?.dense_index_ready)}
            loading={isLoading && !status}
          />
          <ServiceRow
            label="BM25 sparse index"
            ready={Boolean(status?.bm25_index_ready)}
            loading={isLoading && !status}
          />
          <ServiceRow
            label="Reranker model (BGE)"
            ready={Boolean(status?.reranker_ready)}
            loading={isLoading && !status}
          />
          <ServiceRow
            label="Quality retrieval pipeline"
            ready={Boolean(status?.quality_ready)}
            loading={isLoading && !status}
          />
          <ServiceRow
            label="LLM local inference"
            ready={Boolean(status?.llm_ready)}
            loading={isLoading && !status}
            isLast={true}
          />
        </View>

        {/* LLM Engine Info Section */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Feather name="cpu" size={16} color={colors.ink} />
            <Text style={styles.cardTitle}>LLM Generation Engine</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Backend</Text>
            <Text style={styles.infoValue}>{status?.llm_backend || 'llama-cpp'}</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Model</Text>
            <Text style={styles.infoValue} numberOfLines={1}>
              {status?.llm_model || 'Qwen3-4B-GGUF'}
            </Text>
          </View>

          <View style={[styles.infoRow, styles.infoRowLast]}>
            <Text style={styles.infoLabel}>Execution</Text>
            <Text style={styles.infoValue}>100% Offline Local CPU</Text>
          </View>
        </View>

        {/* Knowledge Base & Catalog Stats */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Feather name="database" size={16} color={colors.ink} />
            <Text style={styles.cardTitle}>Knowledge Base Stats</Text>
          </View>

          <View style={styles.statsGrid}>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{status?.document_count ?? 0}</Text>
              <Text style={styles.statLabel}>Total Docs</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={[styles.statNumber, { color: colors.success }]}>
                {status?.indexed_document_count ?? 0}
              </Text>
              <Text style={styles.statLabel}>Indexed</Text>
            </View>
            <View style={styles.statBox}>
              <Text
                style={[
                  styles.statNumber,
                  queueSize > 0 || isQueueActive ? { color: colors.warning } : {},
                ]}
              >
                {queueSize}
              </Text>
              <Text style={styles.statLabel}>
                {isQueueActive ? 'Processing' : 'In Queue'}
              </Text>
            </View>
          </View>

          {sourceStatus?.source_dir ? (
            <View style={styles.sourceSyncBox}>
              <View style={styles.sourceSyncHeader}>
                <Feather name="folder" size={14} color={colors.muted} />
                <Text style={styles.sourceSyncDir} numberOfLines={1}>
                  {sourceStatus.source_dir}
                </Text>
              </View>
              <Text style={styles.sourceSyncMeta}>
                Status: {sourceStatus.status} · {sourceStatus.indexed} synced files
              </Text>
            </View>
          ) : null}
        </View>

        {/* Server Connection Info */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Feather name="server" size={16} color={colors.ink} />
            <Text style={styles.cardTitle}>Server Connection</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Server URL</Text>
            <Text style={styles.infoValue} numberOfLines={1}>
              {serverUrl || 'Not configured'}
            </Text>
          </View>

          <View style={[styles.infoRow, styles.infoRowLast]}>
            <Text style={styles.infoLabel}>Last Updated</Text>
            <Text style={styles.infoValue}>{formatTime(lastUpdated)}</Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={styles.refreshButton}
            onPress={() => fetchStatus(true)}
            disabled={isRefreshing}
            activeOpacity={0.8}
          >
            <Feather name="refresh-cw" size={16} color={colors.ink} />
            <Text style={styles.refreshButtonText}>
              {isRefreshing ? 'Refreshing...' : 'Refresh Status'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.changeServerButton}
            onPress={() => router.push('/config')}
            activeOpacity={0.7}
          >
            <Feather name="settings" size={14} color={colors.muted} />
            <Text style={styles.changeServerText}>Change Server Address</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
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
  headerButton: {
    padding: 6,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: spacing.lg,
    gap: spacing.lg,
    paddingBottom: spacing.xl + 20,
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: '#fee2e2',
    borderColor: '#fca5a5',
    borderWidth: 1,
    borderRadius: radii.md,
    padding: spacing.md,
  },
  errorText: {
    fontSize: fontSize.xs,
    color: colors.error,
    fontWeight: '500',
    flex: 1,
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
    borderRadius: radii.lg,
    padding: spacing.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.md,
    paddingBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  cardTitle: {
    fontSize: fontSize.base,
    fontWeight: '700',
    color: colors.ink,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  infoRowLast: {
    borderBottomWidth: 0,
    paddingBottom: 0,
  },
  infoLabel: {
    fontSize: fontSize.sm,
    color: colors.muted,
  },
  infoValue: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.ink,
    maxWidth: '65%',
    textAlign: 'right',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  statBox: {
    flex: 1,
    backgroundColor: colors.canvas,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.line,
    paddingVertical: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statNumber: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.ink,
    marginBottom: 2,
  },
  statLabel: {
    fontSize: fontSize.xs,
    color: colors.muted,
    fontWeight: '500',
  },
  sourceSyncBox: {
    marginTop: spacing.md,
    padding: spacing.sm + 2,
    backgroundColor: colors.canvas,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.line,
  },
  sourceSyncHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  sourceSyncDir: {
    fontSize: fontSize.xs,
    fontWeight: '600',
    color: colors.ink,
    flex: 1,
  },
  sourceSyncMeta: {
    fontSize: fontSize.xs,
    color: colors.muted,
  },
  actionsContainer: {
    gap: spacing.md,
    marginTop: spacing.xs,
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderColor: colors.ink,
    borderWidth: 1.5,
    borderRadius: radii.md,
    height: 48,
  },
  refreshButtonText: {
    fontSize: fontSize.base,
    fontWeight: '600',
    color: colors.ink,
  },
  changeServerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: spacing.sm,
  },
  changeServerText: {
    fontSize: fontSize.sm,
    color: colors.muted,
    fontWeight: '500',
  },
});
