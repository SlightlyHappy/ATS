import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold text-slate-900 dark:text-white">404</h1>
        <h2 className="text-2xl font-semibold text-slate-700 dark:text-slate-300">Page Not Found</h2>
        <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Button asChild>
          <Link href="/">
            Return Home
          </Link>
        </Button>
      </div>
    </div>
  );
}
