/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    proxyTimeout: 120000, // Timeout in milliseconds (2 minutes)
  },
  async rewrites() {
    return [
      // Chat
      {
        source: '/chat',
        destination: 'http://127.0.0.1:8000/chat/',
      },
      {
        source: '/chat/:path*',
        destination: 'http://127.0.0.1:8000/chat/:path*',
      },
      // Upload
      {
        source: '/upload',
        destination: 'http://127.0.0.1:8000/upload/',
      },
      {
        source: '/upload/:path*',
        destination: 'http://127.0.0.1:8000/upload/:path*',
      },
      // Test
      {
        source: '/test',
        destination: 'http://127.0.0.1:8000/test/',
      },
      {
        source: '/test/:path*',
        destination: 'http://127.0.0.1:8000/test/:path*',
      },
    ];
  },
};

export default nextConfig;
