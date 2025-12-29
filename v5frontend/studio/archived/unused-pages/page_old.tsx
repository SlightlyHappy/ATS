'use client';
import Link from 'next/link';
import * as React from 'react';
import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Button } from '@/components/ui/button';
import { AppLogo } from '@/components/shared/app-logo';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  HiMiniCpuChip, 
  HiShieldCheck, 
  HiArrowRight, 
  HiPlay,
  HiRocketLaunch,
  HiBars3,
  HiXMark,
  HiSparkles,
  HiEye,
  HiBolt
} from 'react-icons/hi2';
import { TbBrain, TbRobot } from 'react-icons/tb';
import { BsPeopleFill } from 'react-icons/bs';
import { ThemeToggle } from '@/components/shared/theme-toggle';

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

// Enhanced Premium GSAP Animations Hook
const usePremiumAnimations = () => {
  const heroRef = useRef<HTMLElement>(null);
  const statsRef = useRef<HTMLElement>(null);
  const agentsRef = useRef<HTMLElement>(null);
  const showcaseRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const ctx = gsap.context(() => {
      // Premium Hero Animation Sequence
      const tl = gsap.timeline();
      
      tl.from('.hero-title', {
        y: 100,
        opacity: 0,
        duration: 1.2,
        ease: "power4.out"
      })
      .from('.hero-subtitle', {
        y: 60,
        opacity: 0,
        duration: 1,
        ease: "power3.out"
      }, "-=0.6")
      .from('.hero-cta', {
        y: 40,
        opacity: 0,
        duration: 0.8,
        ease: "power2.out"
      }, "-=0.4")
      .from('.hero-visual', {
        scale: 0.8,
        opacity: 0,
        duration: 1.5,
        ease: "power3.out"
      }, "-=0.8");

      // Floating elements animation
      gsap.to('.float-1', {
        y: -20,
        duration: 3,
        ease: "power1.inOut",
        repeat: -1,
        yoyo: true
      });

      gsap.to('.float-2', {
        y: -15,
        duration: 2.5,
        ease: "power1.inOut",
        repeat: -1,
        yoyo: true,
        delay: 0.5
      });

      gsap.to('.float-3', {
        y: -25,
        duration: 3.5,
        ease: "power1.inOut",
        repeat: -1,
        yoyo: true,
        delay: 1
      });

      // Stats Counter Animation
      gsap.from('.stat-number', {
        scrollTrigger: {
          trigger: statsRef.current,
          start: "top 70%",
          toggleActions: "play none none reverse"
        },
        textContent: 0,
        duration: 2,
        ease: "power2.out",
        snap: { textContent: 1 },
        stagger: 0.2
      });

      gsap.from('.stat-card', {
        scrollTrigger: {
          trigger: statsRef.current,
          start: "top 75%",
          toggleActions: "play none none reverse"
        },
        y: 80,
        opacity: 0,
        duration: 1.2,
        stagger: 0.15,
        ease: "power3.out"
      });

      // Agent Cards Reveal
      gsap.from('.agent-card', {
        scrollTrigger: {
          trigger: agentsRef.current,
          start: "top 70%",
          toggleActions: "play none none reverse"
        },
        y: 100,
        opacity: 0,
        rotation: 5,
        duration: 1.5,
        stagger: 0.2,
        ease: "power4.out"
      });

      // Interactive showcase animations
      gsap.from('.showcase-item', {
        scrollTrigger: {
          trigger: showcaseRef.current,
          start: "top 80%",
          end: "bottom 20%",
          scrub: 1,
          toggleActions: "play none none reverse"
        },
        x: (index) => index % 2 === 0 ? -100 : 100,
        opacity: 0,
        duration: 2,
        stagger: 0.3,
        ease: "power2.out"
      });

      // CTA Reveal
      gsap.from('.cta-content', {
        scrollTrigger: {
          trigger: ctaRef.current,
          start: "top 85%",
          toggleActions: "play none none reverse"
        },
        y: 60,
        opacity: 0,
        duration: 1.2,
        ease: "power3.out"
      });

      // Continuous background gradient animation
      gsap.to('.gradient-bg', {
        backgroundPosition: "200% center",
        duration: 8,
        ease: "none",
        repeat: -1
      });

    });

    return () => ctx.revert();
  }, []);

  return { heroRef, statsRef, agentsRef, showcaseRef, ctaRef };
};

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [activeAgent, setActiveAgent] = useState(0);
  const { heroRef, statsRef, agentsRef, showcaseRef, ctaRef } = usePremiumAnimations();

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
                AI Agents
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
              <Button asChild className="hidden sm:inline-flex" size="sm">
                <Link href="/candidates">For Candidates</Link>
              </Button>
            </div>
          </div>
          
          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t">
              <nav className="flex flex-col space-y-4 p-4">
                <Link href="#features" className="text-sm font-medium" onClick={() => setMobileMenuOpen(false)}>AI Agents</Link>
                <Link href="#about" className="text-sm font-medium" onClick={() => setMobileMenuOpen(false)}>About</Link>
                <Link href="#contact" className="text-sm font-medium" onClick={() => setMobileMenuOpen(false)}>Contact</Link>
                <div className="pt-2">
                  <Button asChild size="sm" className="w-full">
                    <Link href="/candidates">For Candidates</Link>
                  </Button>
                </div>
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
              {/* Premium Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full text-sm font-medium mb-4">
                <span className="text-blue-600">✨</span>
                <span>Bear Systems - BearSystemsHRT© AI Revolution</span>
              </div>
              
              <h1 className="text-5xl md:text-7xl lg:text-8xl font-light tracking-tight text-slate-900 dark:text-white">
                Revolutionary
                <span className="block font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Agentic HR
                </span>
                <span className="block font-light">Intelligence Platform</span>
              </h1>
              
              <p className="text-xl md:text-2xl text-slate-600 dark:text-slate-300 font-light max-w-3xl mx-auto">
                Experience tomorrow's Human Resources today with our groundbreaking agentic systems
              </p>
              
              {/* Value Proposition */}
              <div className="bg-slate-50 dark:bg-slate-800 rounded-2xl p-6 max-w-3xl mx-auto my-8">
                <p className="text-lg text-slate-700 dark:text-slate-300">
                  Witness autonomous AI agents transform your{' '}
                  <span className="font-semibold text-red-600">₹5,00,000 HR operations</span>
                  {' '}into{' '}
                  <span className="font-semibold text-emerald-600">₹50,000 of pure AI-driven intelligence</span>
                </p>
              </div>
              
              <div className="pt-8 hero-animate">
                <Button size="lg" className="text-lg px-8 py-4 rounded-full bg-blue-600 hover:bg-blue-700">
                  <a href="mailto:admin@bearsystems.co.in?subject=Experience%20the%20Future%20Now%20-%20BearSystemsHRT%20Demo%20Request" className="flex items-center gap-2">
                    Experience the Future Now
                  </a>
                </Button>
              </div>
              
              {/* Trust Indicators */}
              <div className="pt-8">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 font-medium tracking-wider uppercase">Trusted by Enterprise Leaders</p>
                <div className="flex items-center justify-center gap-8 opacity-60">
                  <div className="w-2 h-2 bg-slate-300 dark:bg-slate-600 rounded-full"></div>
                  <div className="w-3 h-3 bg-slate-400 dark:bg-slate-500 rounded-full"></div>
                  <div className="w-4 h-4 bg-slate-500 dark:bg-slate-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-slate-400 dark:bg-slate-500 rounded-full"></div>
                  <div className="w-2 h-2 bg-slate-300 dark:bg-slate-600 rounded-full"></div>
                </div>
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
        </section>        {/* Intelligence Showcase */}
        <section ref={statsRef} className="py-32 bg-slate-50 dark:bg-slate-900">
          <div className="container px-6">
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-6">
                Intelligence that
                <span className="block font-semibold">delivers results</span>
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
                Transform <span className="font-semibold text-red-600">₹5,00,000 HR operations</span> into <span className="font-semibold text-emerald-600">₹50,000 of pure AI-driven intelligence</span>
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-16 max-w-6xl mx-auto">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="text-center stat-card cursor-pointer hover:scale-105 transition-transform duration-300">
                      <div className="text-6xl md:text-7xl font-light text-blue-600 mb-4">95%</div>
                      <p className="text-xl text-slate-600 dark:text-slate-300">Intelligence boost</p>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>1000x faster decisions with 99.2% accuracy</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="text-center stat-card cursor-pointer hover:scale-105 transition-transform duration-300">
                      <div className="text-6xl md:text-7xl font-light text-purple-600 mb-4">₹2.5Cr</div>
                      <p className="text-xl text-slate-600 dark:text-slate-300">Value generated</p>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Cost savings + efficiency gains + risk mitigation</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="text-center stat-card cursor-pointer hover:scale-105 transition-transform duration-300">
                      <div className="text-6xl md:text-7xl font-light text-indigo-600 mb-4">60%</div>
                      <p className="text-xl text-slate-600 dark:text-slate-300">Better talent match</p>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Superior cultural fit with zero bias detection</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
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

        {/* Product Capabilities Section */}
        <section className="py-32 bg-slate-50 dark:bg-slate-900">
          <div className="container px-6 text-center">
            <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-8">
              End-to-end
              <span className="block font-semibold">HR orchestration</span>
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 mb-12 max-w-3xl mx-auto">
              From recruitment intelligence to compliance mastery, performance tracking to payroll optimization — complete autonomous HR transformation
            </p>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
              <div className="p-6 bg-white dark:bg-slate-800 rounded-2xl shadow-lg">
                <div className="w-12 h-12 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                  <span className="text-white text-2xl">🧠</span>
                </div>
                <h3 className="font-semibold mb-2">Recruitment Intelligence</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300">500K+ Indian hiring scenarios</p>
              </div>
              
              <div className="p-6 bg-white dark:bg-slate-800 rounded-2xl shadow-lg">
                <div className="w-12 h-12 mx-auto mb-4 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center">
                  <span className="text-white text-2xl">⚖️</span>
                </div>
                <h3 className="font-semibold mb-2">Legal Compliance</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300">Indian Labor Law automation</p>
              </div>
              
              <div className="p-6 bg-white dark:bg-slate-800 rounded-2xl shadow-lg">
                <div className="w-12 h-12 mx-auto mb-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <span className="text-white text-2xl">📈</span>
                </div>
                <h3 className="font-semibold mb-2">Performance Tracking</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300">Real-time intelligence monitoring</p>
              </div>
              
              <div className="p-6 bg-white dark:bg-slate-800 rounded-2xl shadow-lg">
                <div className="w-12 h-12 mx-auto mb-4 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                  <span className="text-white text-2xl">💰</span>
                </div>
                <h3 className="font-semibold mb-2">Payroll Optimization</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300">Autonomous benefits management</p>
              </div>
            </div>
            
            {/* Key Statistics */}
            <div className="mt-16 grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">AES-256</div>
                <p className="text-sm text-slate-600 dark:text-slate-300">Military-grade encryption</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-emerald-600 mb-2">80%</div>
                <p className="text-sm text-slate-600 dark:text-slate-300">Infrastructure cost reduction</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-2">SOC 2</div>
                <p className="text-sm text-slate-600 dark:text-slate-300">Compliance intelligence</p>
              </div>
            </div>
          </div>
        </section>

        {/* Competitive Advantage Section */}
        <section className="py-32">
          <div className="container px-6">
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-6">
                Why BearSystemsHRT©
                <span className="block font-semibold">pioneers the future</span>
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
                While others deliver fragmented solutions, we orchestrate complete HR transformation through proprietary agentic intelligence
              </p>
            </div>
            
            {/* Comparison Grid */}
            <div className="max-w-6xl mx-auto">
              <div className="grid md:grid-cols-3 gap-8 text-center">
                <div className="p-6">
                  <h3 className="text-lg font-semibold mb-4 text-slate-600">Traditional HR</h3>
                  <div className="space-y-3 text-sm text-slate-500">
                    <div>Point solutions only</div>
                    <div>Manual keyword matching</div>
                    <div>Generic global data</div>
                    <div>Manual compliance checking</div>
                    <div>Basic password protection</div>
                  </div>
                </div>
                
                <div className="p-6">
                  <h3 className="text-lg font-semibold mb-4 text-slate-600">Basic AI Solutions</h3>
                  <div className="space-y-3 text-sm text-slate-500">
                    <div>Limited modules</div>
                    <div>Single AI model scanning</div>
                    <div>Basic training sets</div>
                    <div>Generic global compliance</div>
                    <div>Standard encryption</div>
                  </div>
                </div>
                
                <div className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-2xl border-2 border-blue-200 dark:border-blue-800">
                  <h3 className="text-lg font-semibold mb-4 text-blue-600">BearSystemsHRT©</h3>
                  <div className="space-y-3 text-sm font-medium text-slate-700 dark:text-slate-300">
                    <div>Complete end-to-end agentic HR intelligence</div>
                    <div>Proprietary agentic recruitment + legal intelligence models</div>
                    <div>500K+ Indian hiring scenarios with agentic learning</div>
                    <div>Built-in Indian labor law agentic engine</div>
                    <div>AES-256 + compressed agentic storage</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section ref={ctaRef} id="contact" className="py-32">
            <div className="container px-6 text-center">
              <div className="max-w-4xl mx-auto space-y-8 cta-animate">
                <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white">
                  Ready to transform
                  <span className="block font-semibold">your hiring?</span>
                </h2>
                <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto mb-8">
                  Join forward-thinking companies already experiencing <span className="font-semibold text-emerald-600">90% cost reduction</span> and <span className="font-semibold text-blue-600">10x enhanced talent outcomes</span> through our proprietary AI models
                </p>
                
                {/* Contact Information */}
                <div className="bg-slate-50 dark:bg-slate-800 rounded-2xl p-8 max-w-2xl mx-auto mb-8">
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-lg">
                      <span className="text-2xl">📧</span>
                    </div>
                    <div>
                      <p className="font-bold text-lg text-slate-900 dark:text-white">admin@bearsystems.co.in</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">AI Intelligence Response within 24 hours</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                  <Button size="lg" className="text-lg px-8 py-4 rounded-full bg-blue-600 hover:bg-blue-700 cta-animate">
                    <a href="mailto:admin@bearsystems.co.in?subject=Experience%20the%20Future%20Now%20-%20BearSystemsHRT%20Demo%20Request" className="flex items-center gap-2">
                      Start Free Trial
                    </a>
                  </Button>
                  <Button size="lg" variant="outline" className="text-lg px-8 py-4 rounded-full cta-animate">
                    <Link href="#features">
                      Discover AI Agents
                    </Link>
                  </Button>
                </div>
                
                {/* User Journey Links */}
                <div className="flex flex-wrap justify-center gap-4 pt-8 text-sm">
                  <Link href="/candidates" className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-emerald-600 transition-colors">
                    <span>For Candidates</span>
                    <HiArrowRight className="w-4 h-4" />
                  </Link>
                  <div className="w-px h-4 bg-slate-300 dark:bg-slate-600"></div>
                  <a href="mailto:admin@bearsystems.co.in?subject=Partnership%20Inquiry" className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-blue-600 transition-colors">
                    <span>Partnership</span>
                    <HiArrowRight className="w-4 h-4" />
                  </a>
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
                  <span className="text-xl font-bold">Bear Systems <span className="text-blue-600">HRT</span></span>
                </Link>
                <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
                  Complete agentic HR intelligence platform powered by proprietary AI models. BearSystemsHRT© orchestrates recruitment, compliance, and workforce intelligence.
                </p>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">📧</span>
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">admin@bearsystems.co.in</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🌍</span>
                    <span className="text-sm text-slate-600 dark:text-slate-400">India</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Platform</h3>
                <div className="space-y-3 text-sm">
                  <Link href="#features" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">AI Agents</Link>
                  <Link href="/candidates" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">For Candidates</Link>
                  <a href="mailto:admin@bearsystems.co.in?subject=Demo%20Request" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Request Demo</a>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Company</h3>
                <div className="space-y-3 text-sm">
                  <Link href="#about" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">About</Link>
                  <a href="https://bearsystems.co.in" target="_blank" rel="noopener noreferrer" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">BearSystems.co.in</a>
                  <Link href="#contact" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Contact</Link>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Legal</h3>
                <div className="space-y-3 text-sm">
                  <Link href="/privacy" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Privacy</Link>
                  <Link href="/terms" className="block text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">Terms</Link>
                  <span className="block text-slate-600 dark:text-slate-300">Enterprise Security</span>
                </div>
              </div>
            </div>
            
            <div className="border-t mt-12 pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-slate-600 dark:text-slate-300">
              <p>&copy; 2025 Bear Systems HRT. A proud product of BearSystems.co.in.</p>
              <p>Agentic Intelligence Response within 24 hours</p>
            </div>
          </div>
        </footer>
      </div>
    </TooltipProvider>
  );
}
