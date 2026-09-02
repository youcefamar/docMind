# DocMind Mobile — Execution Plan

> **Read first:** [`mobile-ui-design.md`](./mobile-ui-design.md) — this plan references it throughout.
> **Agent:** Follow phases sequentially. Do not start a phase until the previous phase's verification step passes.
> **Stack:** Expo SDK 57, React Native 0.86, TypeScript 6, React Navigation v7.

---

## Ground Rules for the Executing Agent

1. **Read `mobile-ui-design.md` before writing any code.**
2. All code lives in `mobile-app/`. Never modify `backend/` or `frontend/`.
3. Run `npx expo start` to verify the app launches before marking a phase done.
4. One component per file. No god-components.
5. TypeScript strict mode. No `any`. No `@ts-ignore`.
6. Do not install packages not listed in the phase. Ask first if you need something not listed.
7. Every phase ends with a **Verification checklist** — complete every item before moving on.
8. Color tokens, font sizes, and spacing values must come from `mobile-app/lib/theme.ts` (created in Phase 1), never hardcoded inline.

---

## Phase 0 — Prerequisite Check

**Goal:** Confirm the environment is ready before touching any code.

### Steps

1. Confirm `mobile-app/` exists and has `package.json` with Expo SDK 57.
2. Run `npm install` inside `mobile-app/` to ensure `node_modules` are present.
3. Run `npx expo doctor` and fix any reported issues.
4. Confirm the backend is running and reachable at some local URL (e.g. `http://localhost:8000`) before starting integration work.

### Verification

- [ ] `npx expo start` launches without errors.
- [ ] No red warnings from `expo doctor`.

---

## Phase 1 — Project Scaffold & Theme

**Goal:** Wire up navigation shell, design tokens, and shared utilities. No real UI yet — just the skeleton.

### Packages to install

```bash
cd mobile-app
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install react-native-svg
npx expo install expo-font expo-secure-store expo-document-picker expo-status-bar
```

> Note: `react-native-gesture-handler` and `react-native-reanimated` are needed for bottom sheets (Phase 3). Install them now to avoid a second native rebuild.

```bash
npm install react-native-gesture-handler react-native-reanimated @gorhom/bottom-sheet
npm install react-native-markdown-display
```

Add to `app.json` under `expo.plugins`:
```json
["react-native-reanimated/plugin"]
```

### Files to create

#### `mobile-app/lib/theme.ts`

Define every design token from `mobile-ui-design.md §1`:

```ts
export const colors = {
  canvas: '#f7f9fa',
  ink: '#171a1d',
  muted: '#697079',
  line: '#e6e9eb',
  surface: '#ffffff',
  success: '#059669',
  warning: '#d97706',
  error: '#e11d48',
  chipActive: '#171a1d',
  chipInactive: '#f1f3f4',
  chipInactiveText: '#646b72',
  tabActive: '#171a1d',
  tabInactive: '#9aa1a8',
} as const;

export const radii = {
  sm: 8,
  md: 12,
  lg: 16,
  pill: 24,
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
} as const;

export const fontSize = {
  xs: 10,
  sm: 11,
  md: 13,
  base: 14,
  lg: 15,
  xl: 17,
  xxl: 18,
} as const;
```

#### `mobile-app/lib/api.ts`

Mirror `frontend/lib/api.ts`. Add `getBaseUrl()` that reads from `expo-secure-store`:

```ts
import * as SecureStore from 'expo-secure-store';

const BASE_URL_KEY = 'docmind.server_url';

export async function getBaseUrl(): Promise<string> {
  const stored = await SecureStore.getItemAsync(BASE_URL_KEY);
  return stored ?? '';
}

export async function saveBaseUrl(url: string): Promise<void> {
  await SecureStore.setItemAsync(BASE_URL_KEY, url.replace(/\/$/, ''));
}

export async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const base = await getBaseUrl();
  return fetch(`${base}${path}`, options);
}

export async function readApiPayload<T>(res: Response): Promise<T | null> {
  try {
    const json = await res.json();
    return (json?.data ?? json) as T;
  } catch {
    return null;
  }
}

export async function getApiErrorMessage(res: Response): Promise<string> {
  try {
    const json = await res.json();
    return json?.error ?? json?.detail ?? `HTTP ${res.status}`;
  } catch {
    return `HTTP ${res.status}`;
  }
}
```

#### `mobile-app/app/` directory structure to create

```
mobile-app/
├── app/
│   ├── (tabs)/
│   │   ├── _layout.tsx      ← Bottom tab navigator
│   │   ├── chat.tsx         ← Chat screen (placeholder)
│   │   ├── documents.tsx    ← Documents screen (placeholder)
│   │   └── status.tsx       ← Status screen (placeholder)
│   ├── config.tsx           ← First-run config screen
│   └── _layout.tsx          ← Root layout (NavigationContainer + GestureHandlerRootView)
├── components/
│   ├── AppHeader.tsx
│   ├── StatusDot.tsx
│   ├── CategoryBadge.tsx
│   ├── Toast.tsx
│   ├── ConfirmSheet.tsx
│   └── EmptyState.tsx
└── lib/
    ├── theme.ts
    └── api.ts
```

> **Note:** This project uses Expo Router (file-based routing). The `app/` directory replaces the old `App.tsx` entry point. Update `package.json` `"main"` to `"expo-router/entry"` and add `"expo-router"` to dependencies.

```bash
npx expo install expo-router
```

Update `app.json`:
```json
{
  "expo": {
    "scheme": "docmind",
    ...
  }
}
```

#### `mobile-app/app/_layout.tsx`

```tsx
import 'react-native-gesture-handler';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Slot } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar style="dark" />
      <Slot />
    </GestureHandlerRootView>
  );
}
```

#### `mobile-app/app/(tabs)/_layout.tsx`

Implement the 3-tab bar exactly as specified in `mobile-ui-design.md §3`.
Use `MessageSquare`, `Database`, `Cpu` icons from `react-native-vector-icons/Feather` (bundled with Expo via `@expo/vector-icons`).

Tabs: `chat` (label "Chat"), `documents` (label "Docs"), `status` (label "Status").

Tab bar style:
- `tabBarActiveTintColor`: `colors.tabActive`
- `tabBarInactiveTintColor`: `colors.tabInactive`
- `tabBarStyle.borderTopColor`: `colors.line`
- `tabBarStyle.backgroundColor`: `colors.surface`
- Hide the default header (`headerShown: false`).

#### Placeholder screens

Each placeholder screen must:
- Return a `View` with `flex: 1, backgroundColor: colors.canvas`.
- Show a centered `Text` label: "Chat", "Documents", "Status".
- Import from `lib/theme.ts`.

#### Shared components (stubs — full implementations come in later phases)

Create each file in `mobile-app/components/` as a typed stub that renders `null` or a simple `View`. This lets TypeScript validate imports before the full component is built.

### Verification

- [ ] `npx expo start` launches with no errors or red screens.
- [ ] Bottom tab bar renders with 3 tabs: Chat, Docs, Status.
- [ ] Tapping each tab navigates correctly.
- [ ] Theme tokens are importable from `lib/theme.ts`.
- [ ] `lib/api.ts` compiles without TypeScript errors.

---

## Phase 2 — First-run Config Screen

**Goal:** Implement the API URL entry screen (`mobile-ui-design.md §10`).

### Files to implement

#### `mobile-app/app/config.tsx`

Full implementation:
- `TextInput` pre-filled with `http://192.168.1.x:8000` placeholder.
- "Connect" button: calls `GET /api/status/` via `apiFetch`.
  - On success: saves URL with `saveBaseUrl()`, navigates to `/(tabs)/chat`.
  - On failure: shows inline error text below the input.
- Loading state: button shows spinner + "Connecting…" text.
- BrainCircuit icon at top (use `@expo/vector-icons/Feather` or SVG).

**Logic for deciding which screen to show on launch:**

In `mobile-app/app/index.tsx` (add this file):
```tsx
import { useEffect } from 'react';
import { router } from 'expo-router';
import { getBaseUrl } from '../lib/api';
import { apiFetch } from '../lib/api';

export default function Index() {
  useEffect(() => {
    async function check() {
      const base = await getBaseUrl();
      if (!base) { router.replace('/config'); return; }
      try {
        const res = await apiFetch('/api/status/');
        if (res.ok) { router.replace('/(tabs)/chat'); }
        else { router.replace('/config'); }
      } catch {
        router.replace('/config');
      }
    }
    check();
  }, []);
  return null; // splash handled by Expo
}
```

### Verification

- [ ] First launch (no saved URL) → Config screen appears.
- [ ] Invalid URL → error message appears, no crash.
- [ ] Valid URL → navigates to Chat tab.
- [ ] App relaunch with valid saved URL → skips config, goes to Chat.

---

## Phase 3 — Chat Screen

**Goal:** Full chat UI matching `mobile-ui-design.md §4`.

### Files to implement

#### `mobile-app/components/MessageBubble.tsx`

Props:
```ts
interface MessageBubbleProps {
  sender: 'user' | 'bot';
  content: string;
  timestamp: string;
  sources?: Source[];
  citations?: Citation[];
  isLoading?: boolean;
}
```

- User bubble: right-aligned, dark background, white text. Max width 80%.
- Bot bubble: left-aligned, white bg with border. Max width 92%. Uses `react-native-markdown-display` for content.
- Loading bubble: three animated dots (use `Animated.loop` + `Animated.sequence`).
- After bot content: renders `SourceCard` if sources are present.

#### `mobile-app/components/SourceCard.tsx`

Translate `frontend/components/SourceCard.tsx` to React Native:
- `View` instead of `div`.
- `TouchableOpacity` for expand/collapse.
- `Text` components for all text.
- Same color-hash logic for `CategoryBadge`.
- Same expand/collapse state logic.
- Use `FlatList` (horizontal) if many sources, or simple `map` for ≤5 sources.

#### `mobile-app/components/ProfileChips.tsx`

Props:
```ts
interface ProfileChipsProps {
  selected: 'fast' | 'quality';
  onChange: (profile: 'fast' | 'quality') => void;
}
```

Two chips as described in `mobile-ui-design.md §4.4`. Use `TouchableOpacity`.

#### `mobile-app/components/ChatInput.tsx`

Props:
```ts
interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}
```

- Multiline `TextInput`, grows up to 120dp.
- Send button: dark circle, disabled opacity when `disabled=true` or text empty.
- `KeyboardAvoidingView` wrapper (behavior `'padding'` on iOS, `'height'` on Android).

#### `mobile-app/app/(tabs)/chat.tsx`

State mirrors `ChatWindow.tsx`:
```ts
messages: Message[]
selectedProfile: 'fast' | 'quality'
isLoading: boolean
runtimeStatus: RuntimeStatus | null
```

Session persistence: `AsyncStorage` (install `@react-native-async-storage/async-storage` via `npx expo install`). Same key `docmind.chat-session.v1`, same validation logic, same `MAX_STORED_MESSAGES = 100`.

API call to `POST /api/chat/`:
```ts
const body = {
  question: text,
  profile: selectedProfile,
  chat_history: buildChatHistory(messages),
};
```

On response: parse same JSON structure as web. Append bot message with sources and citations.

Header right actions:
- `StatusDot` component showing LLM readiness.
- `Trash2` icon → `ConfirmSheet` → clears messages, resets to welcome message.

Pull status on mount with `GET /api/status/`.

### Verification

- [ ] Welcome message appears on first launch.
- [ ] Typing a question and tapping Send shows loading bubble then bot answer.
- [ ] Markdown in bot answers renders correctly (bold, code, lists).
- [ ] Sources expand/collapse on tap.
- [ ] Profile chips switch correctly and the correct profile is sent.
- [ ] Chat history persists across app restarts.
- [ ] Clear history works (ConfirmSheet appears, then messages reset).
- [ ] StatusDot reflects actual LLM state.
- [ ] Keyboard does not overlap the input bar on either platform.

---

## Phase 4 — Documents Screen

**Goal:** Full document management UI matching `mobile-ui-design.md §5`.

### Additional packages

```bash
npx expo install expo-document-picker @react-native-async-storage/async-storage
```

(AsyncStorage already installed in Phase 3 if done there first.)

### Files to implement

#### `mobile-app/components/DocumentRow.tsx`

Props:
```ts
interface DocumentRowProps {
  doc: DocumentSummary;
  onDelete: (id: string) => void;
}
```

- Swipeable wrapper (`Swipeable` from `react-native-gesture-handler`): swipe left reveals red "Delete" action button.
- Tap on error-status card: toggles inline error detail visibility.
- Status indicators as specified in `mobile-ui-design.md §5.6`.

#### `mobile-app/components/UploadButton.tsx`

Props:
```ts
interface UploadButtonProps {
  onUploadComplete: () => void;
  categories: string[];
}
```

- "Pick files to upload" button.
- After picking: show `CategorySheet` bottom sheet.
- After category confirmed: upload via `multipart/form-data` POST to `/api/documents/`.
- Linear progress bar during upload (`ActivityIndicator` or a simple animated `View` width).
- Success/error fires `Toast`.

#### `mobile-app/components/CategorySheet.tsx`

Props:
```ts
interface CategorySheetProps {
  visible: boolean;
  categories: string[];
  onSelect: (category: string) => void;
  onClose: () => void;
}
```

- `@gorhom/bottom-sheet` with snap points `['40%', '70%']`.
- List of category options, each a `TouchableOpacity` row.
- "New category" `TextInput` at bottom.
- "Confirm" button.

#### `mobile-app/app/(tabs)/documents.tsx`

State:
```ts
documents: DocumentSummary[]
categories: string[]
searchTerm: string
selectedCategory: string   // '' = All
isLoading: boolean
uploadMessage: { type: 'success' | 'error'; text: string } | null
```

On mount: fetch `GET /api/config/` for categories and `GET /api/documents/` for doc list.
Pull-to-refresh: `refreshing` prop on `FlatList`, triggers refetch.
Header right: `RefreshCw` icon → POST `/api/sources/sync`, then refetch docs.

Filter logic: same as web — filter by `searchTerm` and `selectedCategory` client-side.

Delete: DELETE `/api/documents/{id}` → refetch list.

### Verification

- [ ] Document list loads and displays correctly.
- [ ] Pull-to-refresh works.
- [ ] Search filters the list.
- [ ] Category chips filter the list.
- [ ] File picker opens on tap.
- [ ] Category sheet appears after file is picked.
- [ ] Upload sends file and shows progress.
- [ ] Toast appears on upload success and error.
- [ ] Swipe-left reveals delete action.
- [ ] Delete removes document from list.
- [ ] Error-status documents show error detail on tap.
- [ ] Sync button triggers folder sync.

---

## Phase 5 — Status Screen

**Goal:** Runtime status display matching `mobile-ui-design.md §6`.

### Files to implement

#### `mobile-app/components/ServiceRow.tsx`

Props:
```ts
interface ServiceRowProps {
  label: string;
  ready: boolean;
  loading?: boolean;
}
```

Renders one service row with dot, label, and status text.

#### `mobile-app/app/(tabs)/status.tsx`

State:
```ts
status: RuntimeStatus | null
isLoading: boolean
lastUpdated: Date | null
```

- On screen focus (`useFocusEffect`): fetch `GET /api/status/` immediately, then every 10 seconds.
- Cleanup: clear interval on unfocus.
- "Refresh" full-width outlined button at bottom: manual refetch.
- "Change server" link at the very bottom → navigates to `/config`.

Sections:
1. **Runtime Services**: Embedding, Dense index, BM25 index, Quality retrieval, LLM.
2. **LLM Info**: backend name, model name.
3. **Document Stats**: total, indexed, queue size.

### Verification

- [ ] All 5 service rows render with correct status dots.
- [ ] Dots update when backend state changes.
- [ ] Auto-poll fires every 10s when screen is focused.
- [ ] Auto-poll stops when navigating away.
- [ ] Manual refresh works.
- [ ] "Change server" navigates to config screen.

---

## Phase 6 — Shared Components (Full Implementation)

**Goal:** Fill in the stubs created in Phase 1 with full implementations.

> Most of these will already be implemented as part of Phases 3–5. This phase catches anything remaining.

### Components to finalize

#### `mobile-app/components/AppHeader.tsx`

```ts
interface AppHeaderProps {
  title: string;
  rightActions?: React.ReactNode;
}
```
- `View` with height 56, white bg, `colors.line` bottom border.
- Title: 17sp semibold `colors.ink`.
- `rightActions` positioned absolutely to the right with 12dp padding.

#### `mobile-app/components/Toast.tsx`

- Implemented with `Animated.Value` for slide-in/out.
- Auto-dismiss after 3000ms.
- Swipe-up pan responder to dismiss early.
- Sits at the top of the screen, below the status bar.
- Colors: success=`#dcfce7` with `#059669` text, error=`#fee2e2` with `#e11d48` text.

#### `mobile-app/components/ConfirmSheet.tsx`

- `@gorhom/bottom-sheet` at snap point 30%.
- Two buttons: destructive confirm (red text), cancel (muted text).
- Close on overlay tap or cancel.

#### `mobile-app/components/EmptyState.tsx`

- Vertically centered `View`.
- Icon slot (accept `ReactNode`).
- Title (16sp semibold), subtitle (14sp muted).
- Optional action button below.

### Verification

- [ ] Toast slides in and auto-dismisses.
- [ ] Toast can be swiped up to dismiss.
- [ ] ConfirmSheet appears over content, confirm fires callback, cancel closes it.
- [ ] EmptyState renders correctly in both Chat and Docs screens when no content.
- [ ] AppHeader right actions align correctly.

---

## Phase 7 — Polish & Quality Gates

**Goal:** App-wide polish pass and final verification before the user commits.

### Tasks

1. **Icons:** Replace all placeholder text buttons with proper `@expo/vector-icons` icons. Cross-check every icon against `mobile-ui-design.md`.
2. **Safe areas:** Verify `SafeAreaView` / `useSafeAreaInsets` is applied correctly — no content hidden under notch or home indicator on iOS; no overlap with status bar on Android.
3. **Keyboard:** Test on both iOS simulator and Android emulator that keyboard avoidance works in Chat input.
4. **Loading states:** Every async action (chat send, doc upload, doc list load, status poll) must have a visible loading indicator.
5. **Error states:** Every `fetch` call must handle network errors gracefully (no unhandled promise rejections, no white screens).
6. **Accessibility audit:** Add missing `accessibilityLabel` / `accessibilityRole` props. Verify with the Expo Accessibility Inspector.
7. **TypeScript:** Run `npx tsc --noEmit` — zero errors allowed.
8. **Unused imports:** Remove any unused imports.

### Final verification checklist

- [ ] `npx tsc --noEmit` passes with zero errors.
- [ ] `npx expo start` — no red/yellow warnings in Metro.
- [ ] All 3 tabs function end-to-end against a running backend.
- [ ] Chat: send question, receive answer with sources.
- [ ] Docs: upload a file, see it appear in the list, delete it.
- [ ] Status: all service rows reflect actual backend state.
- [ ] First-run config screen works for a fresh install (clear `expo-secure-store` to test).
- [ ] No `console.error` output during normal use.
- [ ] Safe areas correct on at least one iOS and one Android device/emulator.

---

## Dependency Reference

| Package | Used for | Install command |
|---------|----------|-----------------|
| `expo-router` | File-based navigation | `npx expo install expo-router` |
| `@react-navigation/native` | Navigation core | `npm install @react-navigation/native` |
| `@react-navigation/bottom-tabs` | Tab bar | `npm install @react-navigation/bottom-tabs` |
| `react-native-screens` | Screen optimization | `npm install react-native-screens` |
| `react-native-safe-area-context` | Safe area insets | `npm install react-native-safe-area-context` |
| `expo-font` | Inter font | `npx expo install expo-font` |
| `expo-secure-store` | Server URL storage | `npx expo install expo-secure-store` |
| `expo-document-picker` | File picker | `npx expo install expo-document-picker` |
| `@react-native-async-storage/async-storage` | Chat session storage | `npx expo install @react-native-async-storage/async-storage` |
| `react-native-gesture-handler` | Swipeable rows | `npm install react-native-gesture-handler` |
| `react-native-reanimated` | Animations | `npm install react-native-reanimated` |
| `@gorhom/bottom-sheet` | Bottom sheets | `npm install @gorhom/bottom-sheet` |
| `react-native-markdown-display` | Markdown rendering | `npm install react-native-markdown-display` |
| `@expo/vector-icons` | Lucide-compatible icons | Pre-installed with Expo |

---

## File Tree at Completion

```
mobile-app/
├── app/
│   ├── _layout.tsx              ← Root layout
│   ├── index.tsx                ← First-run check / redirect
│   ├── config.tsx               ← Server URL config screen
│   └── (tabs)/
│       ├── _layout.tsx          ← Bottom tab navigator
│       ├── chat.tsx             ← Chat screen
│       ├── documents.tsx        ← Documents screen
│       └── status.tsx           ← Status screen
├── components/
│   ├── AppHeader.tsx
│   ├── CategoryBadge.tsx
│   ├── CategorySheet.tsx
│   ├── ChatInput.tsx
│   ├── ConfirmSheet.tsx
│   ├── DocumentRow.tsx
│   ├── EmptyState.tsx
│   ├── MessageBubble.tsx
│   ├── ProfileChips.tsx
│   ├── ServiceRow.tsx
│   ├── SourceCard.tsx
│   ├── StatusDot.tsx
│   ├── Toast.tsx
│   └── UploadButton.tsx
├── lib/
│   ├── api.ts
│   └── theme.ts
├── assets/
├── app.json
├── package.json
└── tsconfig.json
```

---

## Risk & Gotchas

| Risk | Mitigation |
|------|-----------|
| `react-native-reanimated` Babel plugin not set up | Add `plugins: ['react-native-reanimated/plugin']` to `babel.config.js` before running |
| `@gorhom/bottom-sheet` requires Reanimated v3 | Ensured by installing together in Phase 1 |
| CORS on Android emulator (localhost ≠ 10.0.2.2) | Document in README: Android emulator uses `10.0.2.2` to reach host machine |
| Expo Router vs bare React Navigation | This plan uses Expo Router (file-based). Do not mix with manual `NavigationContainer` |
| `multipart/form-data` file upload on Android | Use `expo-document-picker` result URI directly in `FormData`; do not read file as blob first |
| `react-native-markdown-display` inline code style | Override default code style in the component to match web app's `#f1f3f4` bg |
