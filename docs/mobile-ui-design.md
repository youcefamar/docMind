# DocMind Mobile — UI Design Specification

> **Purpose:** Defines every screen, component, interaction pattern, and visual token for the DocMind React Native app.
> This is the canonical design reference. The execution plan (`mobile-execution-plan.md`) follows this document.

---

## 1. Design Philosophy

DocMind mobile mirrors the web app's visual identity:

| Token | Value |
|-------|-------|
| Background canvas | `#f7f9fa` |
| Primary ink | `#171a1d` |
| Muted text | `#697079` |
| Border / divider | `#e6e9eb` |
| White surface | `#ffffff` |
| Brand dark accent | `#171a1d` (logo, active tab) |
| Success green | `#059669` (emerald-600) |
| Warning amber | `#d97706` (amber-600) |
| Error rose | `#e11d48` (rose-600) |
| Font | System default (`Inter` fallback via `expo-font`) |
| Corner radius small | `8px` |
| Corner radius medium | `12px` |
| Corner radius large | `16px` |

**Guiding principles:**
- Offline-first feel — status indicators always visible.
- No dark mode in Phase 1 (light only, matching web).
- Accessible tap targets: minimum `44×44 dp`.
- Every destructive action requires a confirmation sheet.

---

## 2. App Structure Overview

```
DocMind Mobile
└── Main Shell
    ├── Tab 1 — Chat          (MessageSquare icon)
    ├── Tab 2 — Documents     (Database icon)
    └── Tab 3 — Status        (Cpu icon)
```

**Navigation pattern:** Native bottom tab bar (`@react-navigation/bottom-tabs`). No drawer. No header stack nav beyond modals.

---

## 3. Bottom Tab Bar

```
┌─────────────────────────────────────────────────┐
│                  [screen content]               │
├─────────────┬──────────────┬────────────────────┤
│  💬 Chat    │  📂 Docs     │  ⚙ Status          │
│  [active]   │              │                    │
└─────────────┴──────────────┴────────────────────┘
```

| Property | Spec |
|----------|------|
| Height | 60dp + safe-area inset |
| Background | `#ffffff` |
| Top border | `1px solid #e6e9eb` |
| Active icon + label color | `#171a1d` |
| Inactive icon + label color | `#9aa1a8` |
| Active indicator | 2dp top line in `#171a1d` on active tab |
| Label font size | 11sp, medium weight |
| Icon size | 22×22dp |

---

## 4. Screen: Chat

Mirrors `ChatWindow.tsx` from the web app.

### 4.1 Layout

```
┌─────────────────────────────────────────────────┐
│  [Header: "DocMind" logo + model status dot]    │  56dp
├─────────────────────────────────────────────────┤
│                                                 │
│  [Message list — FlatList, inverted]            │  flex: 1
│                                                 │
├─────────────────────────────────────────────────┤
│  [Profile chip row: Fast | Quality]             │  40dp
├─────────────────────────────────────────────────┤
│  [Text input] ______________ [Send button]      │  min 52dp
│  [safe area bottom inset]                       │
└─────────────────────────────────────────────────┘
```

### 4.2 Header bar (Chat-specific)

- Left: `BrainCircuit` icon (18dp) in `#171a1d` pill + "DocMind" label (15sp semibold).
- Right: Small status dot — green if LLM ready, amber if loading, red if offline.
- Right: `Trash2` icon button — clears chat history (confirmation bottom sheet).

### 4.3 Message bubbles

**User message:**
```
                ┌──────────────────────────────┐
                │ Your question text here       │
                │                        10:42 │
                └──────────────────────────────┘
```
- Aligned right.
- Background: `#171a1d`, text: `#ffffff`.
- Border radius: 16dp, bottom-right: 4dp.
- Max width: 80% of screen.
- Padding: 12×14dp.

**Bot message:**
```
┌──────────────────────────────────────┐
│ Bot answer with **bold** and         │
│ [S1] citation labels                 │
│                                10:43 │
│ ────────────────────────────────     │
│ ✦ Verified Sources (2)               │
│ [source card]  [source card]         │
└──────────────────────────────────────┘
```
- Aligned left.
- Background: `#ffffff`, border: `1px solid #e6e9eb`.
- Border radius: 16dp, bottom-left: 4dp.
- Max width: 92% of screen.
- Markdown rendering via `react-native-markdown-display`.
- Source cards collapse/expand inline (same logic as `SourceCard.tsx`).

**Loading bubble (streaming indicator):**
- Three animated dots pulse in a bot-style bubble.

**Welcome message:**
- Same as bot bubble, pre-populated with the web app's welcome text.

### 4.4 Profile selector chips

Two horizontally scrollable chips:

| Chip | Icon | Web equivalent |
|------|------|----------------|
| Fast | `Zap` (16dp) | `fast` profile |
| Quality | `Sparkles` (16dp) | `quality` profile |

- Active chip: `background #171a1d`, text `#ffffff`.
- Inactive chip: `background #f1f3f4`, text `#646b72`.
- Border radius: 20dp (pill).
- Padding: 6×14dp.

### 4.5 Input bar

- `TextInput` multiline, maxHeight 120dp, auto-grows.
- Background: `#ffffff`, border: `1px solid #e6e9eb`, border radius: 24dp.
- Placeholder: "Ask something about your docs…"
- Send button: filled circle `#171a1d`, `ArrowUp` icon white, 40×40dp.
- Disabled (no text or loading): send button opacity 0.4.

### 4.6 Source card (inline, below bot message)

Adapted from `SourceCard.tsx`:
- Card background: `#fcfcfb`, border: `1px solid #e8e8e5`, border radius: 12dp.
- Tap to expand excerpt.
- Shows: filename (truncated), category badge (color-hashed), page number, match %.
- Excerpt text: 12sp, italic, color `#697079`.

---

## 5. Screen: Documents

Mirrors `UploadPanel.tsx` + documents list from the web app.

### 5.1 Layout

```
┌─────────────────────────────────────────────────┐
│  [Header: "Documents"]                          │  56dp
│  [Search bar + Filter chip row]                 │  52dp
├─────────────────────────────────────────────────┤
│  [Upload drop zone / file picker button]        │  80dp (collapsed)
├─────────────────────────────────────────────────┤
│                                                 │
│  [Document list — FlatList]                     │  flex: 1
│  - Document row card                            │
│  - Pull-to-refresh                              │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 5.2 Header

- "Documents" in 18sp semibold `#171a1d`.
- Right: `RefreshCw` icon button — triggers folder sync.

### 5.3 Upload zone

Mobile has no drag-and-drop. Replace with:
- A full-width button: `Upload` icon + "Pick files to upload".
- Tapping opens the native file picker via `expo-document-picker`.
- Supported types shown as small tags below: PDF · DOCX · PPTX · XLSX · TXT · MD.
- After picking: shows file name + size + category picker (bottom sheet) + confirm button.
- Upload progress: linear progress bar below the button.
- Success/error: inline toast (green/red banner, auto-dismiss 3s).

### 5.4 Category picker (bottom sheet)

- Modal bottom sheet (`@gorhom/bottom-sheet`).
- Lists available categories fetched from `/api/config/`.
- "New category" input at the bottom.
- Confirm button closes sheet and proceeds with upload.

### 5.5 Search + filter bar

- Full-width search input: `Search` icon prefix, "Search documents…" placeholder.
- Below: horizontally scrollable category filter chips (same style as profile chips).
- "All" chip always first.

### 5.6 Document row card

```
┌──────────────────────────────────────────────────┐
│ [FileText icon]  report_q3.pdf        [status]   │
│                  Finance · 12 pages · 34 chunks  │
│                  Indexed · Sep 2, 2026           │
│                                          [Trash] │
└──────────────────────────────────────────────────┘
```

- Background: `#ffffff`, border: `1px solid #e6e9eb`, border radius: 12dp, margin 8dp horizontal.
- Status badge: `CheckCircle2` green for indexed, `AlertCircle` red for error, animated spinner for processing.
- Delete: swipe-left reveals red delete button (React Native `Swipeable` from `react-native-gesture-handler`), OR tap `Trash2` icon → confirmation alert.
- Tap card when status is error → expands to show error detail inline.

---

## 6. Screen: Status

Mirrors the runtime status panel from `OverviewDashboard.tsx`.

### 6.1 Layout

```
┌─────────────────────────────────────────────────┐
│  [Header: "System Status"]                      │
├─────────────────────────────────────────────────┤
│  [ScrollView]                                   │
│                                                 │
│  ┌─ Runtime Services ──────────────────────────┐│
│  │  ● Embedding model    [Ready / Loading]     ││
│  │  ● Dense index        [Ready / Missing]     ││
│  │  ● BM25 index         [Ready / Missing]     ││
│  │  ● Quality retrieval  [Ready / Degraded]    ││
│  │  ● LLM                [Ready / Loading]     ││
│  └────────────────────────────────────────────┘│
│                                                 │
│  ┌─ LLM Info ──────────────────────────────────┐│
│  │  Backend: llama-cpp                         ││
│  │  Model: Qwen3-4B-GGUF                       ││
│  └────────────────────────────────────────────┘│
│                                                 │
│  ┌─ Document Stats ────────────────────────────┐│
│  │  Total documents: 12                        ││
│  │  Indexed: 11  |  In queue: 1               ││
│  └────────────────────────────────────────────┘│
│                                                 │
│  [Refresh button — full width, outlined]        │
└─────────────────────────────────────────────────┘
```

### 6.2 Service row

- Left: colored dot — green (`#059669`), amber (`#d97706`), red (`#e11d48`).
- Label: service name in 14sp medium `#31363b`.
- Right: status badge text.

### 6.3 Polling

- Auto-refreshes every 10 seconds when screen is focused (`useFocusEffect`).
- Manual refresh button at bottom.

---

## 7. Shared Components

### 7.1 AppHeader

```
Props: title: string, rightActions?: ReactNode[]
Fixed height 56dp, white bg, bottom border #e6e9eb
Title: 17sp semibold #171a1d
```

### 7.2 StatusDot

```
Props: ready: boolean, loading?: boolean
Size: 8×8dp circle
Colors: loading=amber, ready=green, not-ready=red
```

### 7.3 CategoryBadge

```
Props: category: string
Same color-hash algorithm as web SourceCard.tsx
Border + bg + text tinted by hash
```

### 7.4 Toast

```
Props: message: string, type: 'success' | 'error' | 'info'
Appears at top under header, auto-dismisses after 3s
Swipe-up to dismiss early
```

### 7.5 ConfirmSheet

```
A bottom sheet with: title, message, destructive confirm button, cancel button
Used for: clear chat history, delete document
```

### 7.6 EmptyState

```
Props: icon, title: string, subtitle: string, action?: ReactNode
Centered vertically in its flex container
Used when: chat has no messages, docs list is empty
```

---

## 8. API Communication

Mobile talks directly to the same FastAPI backend over the local network.

| Setting | Detail |
|---------|--------|
| Base URL | Saved to `expo-secure-store` after first-run config screen |
| Endpoints used | `/api/chat/`, `/api/documents/`, `/api/config/`, `/api/status/`, `/api/sources/sync` |
| File upload | `multipart/form-data` via `expo-document-picker` + `fetch` |
| Response format | Same JSON envelope as web (`{ data, error }`) |

A shared `mobile-app/lib/api.ts` mirrors `frontend/lib/api.ts` with the same `readApiPayload` and `getApiErrorMessage` helpers, plus a `getBaseUrl()` utility that reads from secure store.

---

## 9. Navigation Flow Diagram

```
App launch
    │
    ▼
[Splash / Config check]
    │   first run: show API URL config screen
    │   subsequent runs: go straight to tab navigator
    ▼
[Bottom Tab Navigator]
    ├─ Tab: Chat
    │     tap source card  → inline expand/collapse
    │     tap trash        → ConfirmSheet → clear history
    │
    ├─ Tab: Documents
    │     tap "Pick files" → expo-document-picker
    │                      → CategorySheet (bottom sheet)
    │                      → upload + progress bar
    │     swipe row left   → delete confirm
    │     tap error row    → expand error detail inline
    │
    └─ Tab: Status
          auto-poll every 10s when focused
          tap Refresh      → manual poll
```

---

## 10. First-run / Config Screen

Shown once if no server URL is saved or the saved URL is unreachable.

```
┌────────────────────────────────────────────────┐
│                                                │
│           [BrainCircuit icon 48dp]             │
│                  DocMind                       │
│                                                │
│   Connect to your local DocMind server         │
│                                                │
│   ┌────────────────────────────────────────┐   │
│   │  http://192.168.1.x:8000               │   │
│   └────────────────────────────────────────┘   │
│                                                │
│   [Connect →]  (full-width button, dark)       │
│                                                │
│   Server must be on the same local network.   │
└────────────────────────────────────────────────┘
```

- URL saved to `expo-secure-store`.
- On "Connect": hit `GET /api/status/` — success → navigate to tabs, fail → inline error message.
- Accessible again via a "Change server" option surfaced in the Status screen footer.

---

## 11. Accessibility

- All interactive elements have `accessibilityLabel` and `accessibilityRole`.
- Color is never the sole conveyor of meaning (icon + color always paired).
- Touch targets minimum `44×44dp`.
- `accessibilityLiveRegion="polite"` on toast and loading states.

---

## 12. What Is NOT in v1

| Feature | Reason |
|---------|--------|
| Dark mode | Scope — add in v2 |
| Push notifications | No backend push support yet |
| Offline document viewing | Out of scope |
| Auth / multi-user | Backend has no auth layer yet |
| Agents tab | Not implemented in web either |
| Settings tab | Not implemented in web either |
| Streaming responses (SSE) | Add after core is working |
| Folder sync UI details | Status screen shows sync state; full sync control is in Docs header |
