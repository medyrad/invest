import js from '@eslint/js';
import ts from 'typescript-eslint';
import next from '@next/eslint-plugin-next';

export default ts.config(
  { ignores: ['.next/**', 'node_modules/**', 'test-results/**', 'playwright-report/**', 'next-env.d.ts'] },
  js.configs.recommended,
  ...ts.configs.recommended,
  {
    languageOptions: { globals: { process: 'readonly', document: 'readonly', innerWidth: 'readonly', fetch: 'readonly' } },
    plugins: { '@next/next': next },
    rules: { ...next.configs.recommended.rules, ...next.configs['core-web-vitals'].rules },
  },
);
