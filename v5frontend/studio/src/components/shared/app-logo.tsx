import * as React from 'react';
import Image from 'next/image';

export function AppLogo() {
  return (
    <div className="relative w-10 h-10 flex items-center justify-center">
      {/* Light theme logo (visible in light mode) */}
      <Image
        src="/images/logo/logo_dark.png"
        alt="Bear Systems HRT Logo"
        width={40}
        height={40}
        className="block dark:hidden object-contain"
        priority
      />
      {/* Dark theme logo (visible in dark mode) */}
      <Image
        src="/images/logo/logo_light.png"
        alt="Bear Systems HRT Logo"
        width={40}
        height={40}
        className="hidden dark:block object-contain"
        priority
      />
    </div>
  );
}
