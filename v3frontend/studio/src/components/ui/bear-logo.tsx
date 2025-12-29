'use client';

import { useTheme } from 'next-themes';
import Image from 'next/image';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

interface BearLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showText?: boolean;
}

const sizeClasses = {
  sm: 'h-6 w-auto',
  md: 'h-8 w-auto',
  lg: 'h-12 w-auto',
  xl: 'h-16 w-auto'
};

const textSizeClasses = {
  sm: 'text-sm',
  md: 'text-lg',
  lg: 'text-xl',
  xl: 'text-2xl'
};

export function BearLogo({ size = 'md', className, showText = true }: BearLogoProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Show a placeholder during hydration
  if (!mounted) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div className={cn("bg-muted rounded", sizeClasses[size])} />
        {showText && (
          <span className={cn("font-bold bg-muted rounded w-24 h-4", textSizeClasses[size])} />
        )}
      </div>
    );
  }

  const logoSrc = resolvedTheme === 'dark' ? '/images/logo/logo_light.png' : '/images/logo/logo_dark.png';

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Image
        src={logoSrc}
        alt="Bear Systems Logo"
        width={64}
        height={64}
        className={cn("object-contain transition-all duration-200", sizeClasses[size])}
        priority
      />
      {showText && (
        <div className="flex flex-col">
          <span className={cn("font-bold tracking-tight", textSizeClasses[size])}>
            Bear Systems
          </span>
          <span className={cn("text-xs text-muted-foreground -mt-1", {
            'text-[10px]': size === 'sm',
            'text-xs': size === 'md' || size === 'lg',
            'text-sm': size === 'xl'
          })}>
            HRT
          </span>
        </div>
      )}
    </div>
  );
}
