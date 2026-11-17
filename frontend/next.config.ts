import type { NextConfig } from 'next';

const upstream = new URL(process.env.BACKEND_INTERNAL_ORIGIN ?? 'http://127.0.0.1:8008');
if (!['http:', 'https:'].includes(upstream.protocol) || upstream.username || upstream.password ||
    upstream.pathname !== '/' || upstream.search || upstream.hash) {
  throw new Error('Invalid BACKEND_INTERNAL_ORIGIN');
}

const config: NextConfig = {
  output: 'standalone',
  images: { loader: 'custom', loaderFile: './src/lib/image-loader.ts' },
  poweredByHeader: false,
  skipTrailingSlashRedirect: true,
  turbopack: { root: process.cwd() },
  async rewrites() {
    return [{ source: '/api/v1/:path*', destination: `${upstream.origin}/api/v1/:path*` }];
  },
};
export default config;
