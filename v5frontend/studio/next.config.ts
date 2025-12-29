import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Performance optimizations
  experimental: {
    optimizePackageImports: [
      'lucide-react', 
      '@radix-ui/react-accordion',
      '@radix-ui/react-alert-dialog',
      '@radix-ui/react-avatar',
      '@radix-ui/react-checkbox',
      '@radix-ui/react-collapsible',
      '@radix-ui/react-dialog',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-label',
      '@radix-ui/react-menubar',
      '@radix-ui/react-popover',
      '@radix-ui/react-progress',
      '@radix-ui/react-radio-group',
      '@radix-ui/react-scroll-area',
      '@radix-ui/react-select',
      '@radix-ui/react-separator',
      '@radix-ui/react-slider',
      '@radix-ui/react-slot',
      '@radix-ui/react-switch',
      '@radix-ui/react-tabs',
      '@radix-ui/react-toast',
      '@radix-ui/react-tooltip',
      'recharts',
      'react-icons/tb',
      'react-icons/ri',
      'react-icons/bs',
      'react-icons/hi'
    ],
    scrollRestoration: true
  },
  
  // Turbopack configuration
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },
  
  // Image optimization
  images: {
    formats: ['image/webp', 'image/avif'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
    ],
    // Add image optimization for better performance
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // Webpack optimization
  webpack: (config, { isServer, dev }) => {
    // Handle Node.js modules on client-side
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        url: false,
        zlib: false,
        http: false,
        https: false,
        assert: false,
        os: false,
        path: false,
      };
    }

    // Server-side webpack configuration for "self is not defined" fix
    if (isServer) {
      config.output = config.output || {};
      config.output.globalObject = 'globalThis';
      config.plugins.push(
        new (require('webpack').BannerPlugin)({
          banner: 'if(typeof globalThis.self==="undefined")globalThis.self=globalThis;',
          raw: true,
          entryOnly: true,
        })
      );
      
      // Debugging: Add stack trace to identify problematic modules
      config.plugins.push(
        new (require('webpack').DefinePlugin)({
          STACK_TRACE: JSON.stringify(new Error().stack)
        })
      );
    }

    // Note: Server polyfill handled via globalObject and BannerPlugin above. Removed global 'self' DefinePlugin and pages/_app entry injection.
    
    // Handle module resolution issues
    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules/,
      type: 'javascript/auto',
    });

    // Production optimizations
    if (!dev) {
      // Only apply aggressive optimizations on the client
      if (!isServer) {
        // Tree shaking optimization
        config.optimization.usedExports = true;
        config.optimization.providedExports = true;
        config.optimization.sideEffects = false;

        // Bundle splitting optimization (client only)
        config.optimization.splitChunks = {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              priority: 10,
              reuseExistingChunk: true,
            },
            ui: {
              test: /[\\/]node_modules[\\/](@radix-ui|lucide-react)[\\/]/,
              name: 'ui',
              priority: 20,
              reuseExistingChunk: true,
            },
            charts: {
              test: /[\\/]node_modules[\\/](recharts)[\\/]/,
              name: 'charts',
              priority: 20,
              reuseExistingChunk: true,
            },
            gsap: {
              test: /[\\/]node_modules[\\/](gsap)[\\/]/,
              name: 'gsap',
              priority: 25,
              reuseExistingChunk: true,
            },
            icons: {
              test: /[\\/]node_modules[\\/](react-icons)[\\/]/,
              name: 'icons',
              priority: 15,
              reuseExistingChunk: true,
            },
          },
        };
      }
    }

    return config;
  },
  
  // Headers for better performance and caching
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains'
          }
        ],
      },
      {
        source: '/api/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=300, stale-while-revalidate=59'
          }
        ],
      },
      {
        source: '/_next/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ],
      },
      {
        source: '/images/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ],
      }
    ];
  },
};

export default nextConfig;
