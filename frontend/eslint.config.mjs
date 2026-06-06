// Minimal flat config for ESLint 10.
// Full rule set (next/core-web-vitals + typescript-eslint) will be added in Epic 2
// once eslint-config-next resolves its FlatCompat circular-reference issue.
// TypeScript correctness is enforced by `npm run type-check` (tsc --noEmit).
export default [
  {
    ignores: ["node_modules/**", ".next/**", "out/**"],
  },
];
