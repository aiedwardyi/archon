
# Rename "Default" to "Studio" in Design Toggle

## Changes

### 1. `src/components/Navbar.tsx`
- Change `designStyle` state type from `"default" | "enterprise"` to `"studio" | "enterprise"`
- Update the Design section array: rename `value: "default"` to `value: "studio"` and `label: "Default"` to `label: "Studio"`
- Reorder the array to show `[ Enterprise, Studio ]` instead of `[ Default, Enterprise ]`
- Add `Pencil` (or use `Sun`) icon for Studio option

### 2. `src/components/ThemeSwitcher.tsx`
- Rename the `"enterprise"` option label/value if applicable -- actually this component only has light/dark/enterprise for color mode, not design style. No changes needed here since the user's request is about the Design section only.

### 3. `src/components/ThemeProvider.tsx`
- No changes needed -- the current ThemeProvider only manages `colorMode` (light/dark). The `designStyle` state lives locally in `Navbar.tsx` and has no presence in ThemeProvider.

## Summary
This is a simple rename in `Navbar.tsx` only: `"default"` becomes `"studio"`, label becomes `"Studio"`, and the order becomes `[ Enterprise | Studio ]`.
