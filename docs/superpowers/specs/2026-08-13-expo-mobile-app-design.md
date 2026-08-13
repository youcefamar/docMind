# Expo Mobile App Design

## Objective

Add a standalone Expo-managed React Native application in `mobile-app/` without
altering the existing Next.js frontend or FastAPI backend.

## Scope

- Use Expo's TypeScript blank starter.
- Install the starter's pinned Expo and React Native dependencies with npm.
- Keep the generated Expo configuration, source entry point, and npm scripts.
- Generate and retain `package-lock.json` for reproducible installs.

## Non-goals

- No mobile screens, navigation, authentication, or backend integration.
- No changes to the existing `frontend/` application.
- No native Android or iOS project directories; Expo will generate them only if
  a future native prebuild is explicitly needed.

## Structure

`mobile-app/` is an independent npm project. Expo runs the TypeScript entry
point through its standard `start`, `android`, `ios`, and `web` scripts.

## Error Handling and Verification

Scaffolding must fail rather than leave a partially initialized project if npm
cannot obtain dependencies. Verification will confirm the generated package
metadata and run Expo's non-interactive project diagnostics where supported.
