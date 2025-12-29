import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
    ],
  },
  webpack: (config, { isServer }) => {
    // Exclude problematic OpenTelemetry packages from client-side builds
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
      };
      
      // Exclude OpenTelemetry modules that cause issues
      config.externals = config.externals || [];
      config.externals.push({
        '@opentelemetry/sdk-logs': 'commonjs @opentelemetry/sdk-logs',
        '@opentelemetry/sdk-node': 'commonjs @opentelemetry/sdk-node',
      });
    }
    
    return config;
  },
};

export default nextConfig;
