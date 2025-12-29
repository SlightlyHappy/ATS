'use client';
import Link from 'next/link';
import * as React from 'react';
import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Button } from '@/components/ui/button';
import { AppLogo } from '@/components/shared/app-logo';
import { 
  HiMiniCpuChip, 
  HiShieldCheck, 
  HiArrowRight, 
  HiPlay,
  HiRocketLaunch,
  HiBars3,
  HiXMark
} from 'react-icons/hi2';
import { TbBrain } from 'react-icons/tb';
import { BsPeopleFill } from 'react-icons/bs';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { TooltipProvider } from '@/components/ui/tooltip';

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

// Apple-Style GSAP Animations Hook
const useSilkAnimations = () => {
  const heroRef = useRef<HTMLElement>(null);
  const statsRef = useRef<HTMLElement>(null);
  const gsapFeaturesRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const ctx = gsap.context(() => {
      // Hero entrance
      gsap.from('.hero-animate', {
        y: 60,
        opacity: 0,
        duration: 1.2,
        stagger: 0.2,
        ease: "power3.out"
      });

      // Stats reveal on scroll
      gsap.from('.stat-card', {
        scrollTrigger: {
          trigger: statsRef.current,
          start: "top 80%",
          toggleActions: "play none none reverse"
        },
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: "power2.out"
      });

      // Feature cards reveal
      gsap.from('.feature-card', {
        scrollTrigger: {
          trigger: gsapFeaturesRef.current,
          start: "top 75%",
          toggleActions: "play none none reverse"
        },
        y: 50,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        ease: "power3.out"
      });

      // CTA section
      gsap.from('.cta-animate', {
        scrollTrigger: {
          trigger: ctaRef.current,
          start: "top 80%",
          toggleActions: "play none none reverse"
        },
        y: 30,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: "power2.out"
      });
    });

    return () => ctx.revert();
  }, []);

  return { heroRef, statsRef, gsapFeaturesRef, ctaRef };
};

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const { heroRef, statsRef, gsapFeaturesRef, ctaRef } = useSilkAnimations();

  return (
    <TooltipProvider>
      <div className="flex min-h-screen flex-col text-foreground relative overflow-hidden">
        
        {/* Header */}
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
          <div className="container flex h-16 items-center justify-between px-4">
            <div className="flex items-center gap-2">
              <AppLogo />
              <span className="text-lg font-semibold">BearSystemsHRT</span>
            </div>
            
            <nav className="hidden md:flex items-center space-x-6">
              <Link href="#features" className="text-sm font-medium transition-colors hover:text-primary">
                Features
              </Link>
              <Link href="#about" className="text-sm font-medium transition-colors hover:text-primary">
                About
              </Link>
              <Link href="#contact" className="text-sm font-medium transition-colors hover:text-primary">
                Contact
              </Link>
            </nav>
            
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button 
                variant="ghost" 
                size="sm"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? (
                  <HiXMark className="h-5 w-5" />
                ) : (
                  <HiBars3 className="h-5 w-5" />
                )}
              </Button>
              <Button asChild className="hidden md:inline-flex">
                <Link href="mailto:admin@bearsystems.co.in">Get Started</Link>
              </Button>
            </div>
          </div>
          
          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t">
              <nav className="flex flex-col space-y-4 p-4">
                <Link href="#features" className="text-sm font-medium">Features</Link>
                <Link href="#about" className="text-sm font-medium">About</Link>
                <Link href="#contact" className="text-sm font-medium">Contact</Link>
                <Button asChild size="sm" className="self-start">
                  <Link href="mailto:admin@bearsystems.co.in">Get Started</Link>
                </Button>
              </nav>
            </div>
          )}
        </header>

        {/* Main Content */}
        <main className="flex-1">
          {/* Apple-Style Hero Section */}
          <section ref={heroRef} className="min-h-screen flex items-center justify-center relative overflow-hidden">
            <div className="container px-6 text-center">
              <div className="max-w-4xl mx-auto space-y-8 hero-animate">
                <h1 className="text-5xl md:text-7xl lg:text-8xl font-light tracking-tight text-slate-900 dark:text-white">
                  The future of
                  <span className="block font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    HR Intelligence
                  </span>
                </h1>
                <p className="text-xl md:text-2xl text-slate-600 dark:text-slate-300 font-light max-w-2xl mx-auto">
                  AI agents that understand talent like never before
                </p>
                <div className="pt-8 hero-animate">
                  <Button size="lg" className="text-lg px-8 py-4 rounded-full bg-blue-600 hover:bg-blue-700">
                    Experience the Demo
                  </Button>
                </div>
              </div>
            </div>
            
            {/* Floating AI Visual */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="relative h-full w-full">
                <div className="absolute top-1/3 left-1/4 w-2 h-2 bg-blue-500 rounded-full animate-pulse opacity-60"></div>
                <div className="absolute top-1/2 right-1/3 w-1 h-1 bg-purple-500 rounded-full animate-pulse opacity-40" style={{animationDelay: '0.5s'}}></div>
                <div className="absolute bottom-1/3 left-1/3 w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse opacity-50" style={{animationDelay: '1s'}}></div>
              </div>
            </div>
          </section>

          {/* Intelligence Showcase */}
          <section ref={statsRef} className="py-32 bg-slate-50 dark:bg-slate-900">
            <div className="container px-6">
              <div className="text-center mb-20">
                <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-6">
                  Intelligence that
                  <span className="block font-semibold">delivers results</span>
                </h2>
              </div>
              
              <div className="grid md:grid-cols-3 gap-16 max-w-6xl mx-auto">
                <div className="text-center stat-card">
                  <div className="text-6xl md:text-7xl font-light text-blue-600 mb-4">95%</div>
                  <p className="text-xl text-slate-600 dark:text-slate-300">Faster hiring decisions</p>
                </div>
                <div className="text-center stat-card">
                  <div className="text-6xl md:text-7xl font-light text-purple-600 mb-4">₹2.5Cr</div>
                  <p className="text-xl text-slate-600 dark:text-slate-300">Value generated</p>
                </div>
                <div className="text-center stat-card">
                  <div className="text-6xl md:text-7xl font-light text-indigo-600 mb-4">60%</div>
                  <p className="text-xl text-slate-600 dark:text-slate-300">Better talent match</p>
                </div>
              </div>
            </div>
          </section>

          {/* AI Agents Showcase */}
          <section ref={gsapFeaturesRef} id="features" className="py-32">
            <div className="container px-6">
              <div className="text-center mb-20">
                <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-6">
                  Meet your
                  <span className="block font-semibold">AI workforce</span>
                </h2>
                <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
                  Four specialized agents working together to transform your HR operations
                </p>
              </div>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
                <div className="text-center p-8 feature-card">
                  <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center">
                    <TbBrain className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Technical Intel</h3>
                  <p className="text-slate-600 dark:text-slate-300">Analyzes skills and technical expertise with precision</p>
                </div>
                
                <div className="text-center p-8 feature-card">
                  <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center">
                    <BsPeopleFill className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Cultural Match</h3>
                  <p className="text-slate-600 dark:text-slate-300">Understands team dynamics and cultural fit</p>
                </div>
                
                <div className="text-center p-8 feature-card">
                  <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl flex items-center justify-center">
                    <HiShieldCheck className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Legal Guard</h3>
                  <p className="text-slate-600 dark:text-slate-300">Ensures compliance and eliminates bias</p>
                </div>
                
                <div className="text-center p-8 feature-card">
                  <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl flex items-center justify-center">
                    <HiMiniCpuChip className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Experience AI</h3>
                  <p className="text-slate-600 dark:text-slate-300">Evaluates career progression and potential</p>
                </div>
              </div>
            </div>
          </section>

          {/* Product Demo Section */}
          <section className="py-32 bg-slate-50 dark:bg-slate-900">
            <div className="container px-6 text-center">
              <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-8">
                See it in
                <span className="block font-semibold">action</span>
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 mb-12 max-w-2xl mx-auto">
                Watch our AI agents analyze, evaluate, and recommend the perfect candidates for your team
              </p>
              
              <div className="relative max-w-5xl mx-auto">
                <div className="aspect-video bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-700 rounded-3xl flex items-center justify-center">
                  <Button size="lg" variant="outline" className="text-lg px-8 py-4 rounded-full">
                    <HiPlay className="w-6 h-6 mr-2" />
                    Watch Demo
                  </Button>
                </div>
              </div>
            </div>
          </section>

          {/* Final CTA */}
          <section ref={ctaRef} className="py-32">
            <div className="container px-6 text-center">
              <div className="max-w-4xl mx-auto space-y-8 cta-animate">
                <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white">
                  Ready to transform
                  <span className="block font-semibold">your hiring?</span>
                </h2>
                <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
                  Join forward-thinking companies already using AI to build better teams
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                  <Button size="lg" className="text-lg px-8 py-4 rounded-full bg-blue-600 hover:bg-blue-700 cta-animate">
                    Start Free Trial
                  </Button>
                  <Button size="lg" variant="outline" className="text-lg px-8 py-4 rounded-full cta-animate">
                    Schedule Demo
                  </Button>
                </div>
              </div>
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="border-t relative overflow-hidden">
          <div className="container py-16 relative z-10">
            <div className="grid md:grid-cols-4 gap-12">
              <div className="space-y-6">
                <Link href="/" className="flex items-center space-x-3 group">
                  <div className="relative">
                    <AppLogo />
                  </div>
                  <span className="text-xl font-bold">BearSystemsHRT</span>
                </Link>
                <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
                  Revolutionizing HR through intelligent agentic systems. Building the future of human resources with AI.
                </p>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Product</h3>
                <div className="space-y-3 text-sm">
                  <Link href="#features" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">AI Agents</Link>
                  <Link href="#" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Analytics</Link>
                  <Link href="#" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Integrations</Link>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Company</h3>
                <div className="space-y-3 text-sm">
                  <Link href="#about" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">About</Link>
                  <Link href="#" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Careers</Link>
                  <Link href="#contact" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Contact</Link>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Legal</h3>
                <div className="space-y-3 text-sm">
                  <Link href="/privacy" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Privacy</Link>
                  <Link href="/terms" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Terms</Link>
                  <Link href="#" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Security</Link>
                </div>
              </div>
            </div>
            
            <div className="border-t mt-12 pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-slate-600 dark:text-slate-300">
              <p>&copy; 2024 Bear Systems. All rights reserved.</p>
              <p>Built with ❤️ for the future of HR</p>
            </div>
          </div>
        </footer>
      </div>
    </TooltipProvider>
  );
}
