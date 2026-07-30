/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  experimental: {
    // TypeScript 7 ships the native compiler as a CLI without the JavaScript
    // compiler API that Next.js previously loaded in-process.
    useTypeScriptCli: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: process.env.BACKEND_URL ? `${process.env.BACKEND_URL}/api/:path*` : 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
