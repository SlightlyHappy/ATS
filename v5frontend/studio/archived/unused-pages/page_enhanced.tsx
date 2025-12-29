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
        duration: 1.4,
        ease: "power4.out"
      })
      .from('.hero-subtitle', {
        y: 60,
        opacity: 0,
        duration: 1.2,
        ease: "power3.out"
      }, "-=0.8")
      .from('.hero-cta', {
        y: 40,
        opacity: 0,
        duration: 1,
        ease: "power2.out"
      }, "-=0.6")
      .from('.hero-visual', {
        scale: 0.8,
        opacity: 0,
        duration: 1.6,
        ease: "power3.out"
      }, "-=1");

      // Floating elements animation
      gsap.to('.float-1', {
        y: -30,
        rotation: 360,
        duration: 20,
        ease: "none",
        repeat: -1
      });

      gsap.to('.float-2', {
        y: -25,
        rotation: -360,
        duration: 25,
        ease: "none",
        repeat: -1,
        delay: 0.5
      });

      gsap.to('.float-3', {
        y: -35,
        rotation: 360,
        duration: 30,
        ease: "none",
        repeat: -1,
        delay: 1
      });

      // Interactive hover effects for floating elements
      const floatingElements = document.querySelectorAll('.float-element');
      floatingElements.forEach((element) => {
        element.addEventListener('mouseenter', () => {
          gsap.to(element, {
            scale: 1.2,
            duration: 0.3,
            ease: "power2.out"
          });
        });
        
        element.addEventListener('mouseleave', () => {
          gsap.to(element, {
            scale: 1,
            duration: 0.3,
            ease: "power2.out"
          });
        });
      });

      // Enhanced Stats Counter Animation
      const statNumbers = document.querySelectorAll('.stat-number');
      statNumbers.forEach((stat, index) => {
        const finalValue = stat.getAttribute('data-final') || '0';
        
        gsap.from(stat, {
          scrollTrigger: {
            trigger: statsRef.current,
            start: "top 70%",
            toggleActions: "play none none reverse"
          },
          textContent: 0,
          duration: 2.5,
          ease: "power2.out",
          delay: index * 0.2,
          snap: { textContent: 1 },
          onUpdate: function() {
            const value = Math.round(this.progress() * parseInt(finalValue));
            stat.textContent = value + (finalValue.includes('%') ? '%' : '');
          }
        });
      });

      gsap.from('.stat-card', {
        scrollTrigger: {
          trigger: statsRef.current,
          start: "top 75%",
          toggleActions: "play none none reverse"
        },
        y: 120,
        opacity: 0,
        rotation: 10,
        duration: 1.5,
        stagger: 0.2,
        ease: "power4.out"
      });

      // Agent Cards Advanced Reveal
      gsap.from('.agent-card', {
        scrollTrigger: {
          trigger: agentsRef.current,
          start: "top 70%",
          toggleActions: "play none none reverse"
        },
        y: 150,
        opacity: 0,
        rotation: 15,
        scale: 0.8,
        duration: 1.8,
        stagger: 0.25,
        ease: "power4.out"
      });

      // Interactive showcase animations with parallax
      gsap.from('.showcase-item', {
        scrollTrigger: {
          trigger: showcaseRef.current,
          start: "top 80%",
          end: "bottom 20%",
          scrub: 1,
          toggleActions: "play none none reverse"
        },
        x: (index) => index % 2 === 0 ? -150 : 150,
        opacity: 0,
        rotation: (index) => index % 2 === 0 ? -10 : 10,
        duration: 2.5,
        stagger: 0.4,
        ease: "power3.out"
      });

      // Advanced CTA Reveal with magnetic effect
      gsap.from('.cta-content', {
        scrollTrigger: {
          trigger: ctaRef.current,
          start: "top 85%",
          toggleActions: "play none none reverse"
        },
        y: 80,
        opacity: 0,
        scale: 0.9,
        duration: 1.5,
        ease: "power3.out"
      });

      // Continuous background gradient animation
      gsap.to('.gradient-bg', {
        backgroundPosition: "200% center",
        duration: 15,
        ease: "none",
        repeat: -1
      });

      // Particle system animation
      const particles = document.querySelectorAll('.particle');
      particles.forEach((particle, index) => {
        gsap.to(particle, {
          y: -200,
          opacity: 0,
          duration: 5 + Math.random() * 3,
          delay: index * 0.1,
          ease: "power1.out",
          repeat: -1,
          repeatDelay: Math.random() * 2
        });
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

  const agents = [
    {
      name: "Technical Intelligence Agent",
      icon: HiMiniCpuChip,
      color: "from-blue-500 to-cyan-500",
      description: "Autonomous technical skill assessment and coding evaluation",
      capabilities: ["Real-time code analysis", "Technical interview automation", "Skill gap identification"]
    },
    {
      name: "Experience Evaluator Agent", 
      icon: TbBrain,
      color: "from-purple-500 to-pink-500",
      description: "Deep experience analysis and career trajectory mapping",
      capabilities: ["Experience validation", "Growth potential analysis", "Role-fit assessment"]
    },
    {
      name: "Cultural Analyzer Agent",
      icon: BsPeopleFill,
      color: "from-indigo-500 to-purple-500", 
      description: "Cultural fit analysis with zero-bias algorithms",
      capabilities: ["Cultural compatibility", "Team dynamics analysis", "Bias elimination"]
    },
    {
      name: "Legal Compliance Guardian",
      icon: HiShieldCheck,
      color: "from-emerald-500 to-green-500",
      description: "Automated legal compliance and risk assessment",
      capabilities: ["Compliance monitoring", "Risk assessment", "Legal documentation"]
    }
  ];

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
        {/* Enhanced Header */}
        <header className="fixed top-0 w-full bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl border-b border-slate-200 dark:border-slate-800 z-50">
          <div className="container px-6 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center space-x-3 group">
                <div className="relative">
                  <AppLogo />
                  <div className="absolute inset-0 bg-blue-500/20 rounded-lg blur-sm group-hover:blur-none transition-all duration-300"></div>
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-slate-900 to-blue-600 dark:from-white dark:to-blue-400 bg-clip-text text-transparent">
                  Bear Systems <span className="text-blue-600">HRT</span>
                </span>
              </Link>
              
              <nav className="hidden md:flex items-center space-x-8">
                <Link href="#agents" className="text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium">AI Agents</Link>
                <Link href="#showcase" className="text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium">Showcase</Link>
                <Link href="/candidates" className="text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium">For Candidates</Link>
                <Link href="#contact" className="text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium">Contact</Link>
                <ThemeToggle />
              </nav>
              
              <button 
                className="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <HiXMark className="w-6 h-6" /> : <HiBars3 className="w-6 h-6" />}
              </button>
            </div>

            {/* Mobile Menu */}
            {mobileMenuOpen && (
              <div className="md:hidden absolute top-full left-0 right-0 bg-white/95 dark:bg-slate-950/95 backdrop-blur-xl border-b border-slate-200 dark:border-slate-800">
                <div className="px-6 py-6 space-y-4">
                  <Link href="#agents" className="block text-slate-700 dark:text-slate-300 hover:text-blue-600 transition-colors font-medium">AI Agents</Link>
                  <Link href="#showcase" className="block text-slate-700 dark:text-slate-300 hover:text-blue-600 transition-colors font-medium">Showcase</Link>
                  <Link href="/candidates" className="block text-slate-700 dark:text-slate-300 hover:text-blue-600 transition-colors font-medium">For Candidates</Link>
                  <Link href="#contact" className="block text-slate-700 dark:text-slate-300 hover:text-blue-600 transition-colors font-medium">Contact</Link>
                  <ThemeToggle />
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Premium Hero Section */}
        <section ref={heroRef} className="relative min-h-screen flex items-center justify-center overflow-hidden">
          {/* Animated Background */}
          <div className="absolute inset-0 gradient-bg bg-gradient-to-br from-blue-50/50 via-purple-50/30 to-indigo-50/50 dark:from-blue-950/30 dark:via-purple-950/20 dark:to-indigo-950/30 bg-[length:200%_200%]"></div>
          
          {/* Particle System */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className="particle absolute w-1 h-1 bg-blue-500/30 rounded-full"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 3}s`
                }}
              />
            ))}
          </div>
          
          {/* Floating Visual Elements */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <div className="float-1 float-element absolute top-1/4 left-1/6 w-64 h-64 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl cursor-pointer"></div>
            <div className="float-2 float-element absolute top-1/3 right-1/6 w-80 h-80 bg-gradient-to-br from-purple-400/20 to-indigo-400/20 rounded-full blur-3xl cursor-pointer"></div>
            <div className="float-3 float-element absolute bottom-1/4 left-1/3 w-72 h-72 bg-gradient-to-br from-indigo-400/20 to-blue-400/20 rounded-full blur-3xl cursor-pointer"></div>
          </div>

          <div className="container px-6 text-center relative z-10">
            <div className="max-w-6xl mx-auto space-y-12">
              {/* Main Title */}
              <div className="hero-title space-y-6">
                <div className="inline-flex items-center gap-3 px-6 py-3 bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-full border border-slate-200/50 dark:border-slate-700/50 mb-8">
                  <HiSparkles className="w-5 h-5 text-blue-600 animate-pulse" />
                  <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">BearSystemsHRT© - Agentic Intelligence Revolution</span>
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                </div>
                
                <h1 className="text-6xl md:text-8xl lg:text-9xl font-light leading-none">
                  <span className="block text-slate-900 dark:text-white">The Future of</span>
                  <span className="block font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">HR Intelligence</span>
                </h1>
              </div>
              
              {/* Subtitle */}
              <div className="hero-subtitle max-w-4xl mx-auto space-y-6">
                <p className="text-xl md:text-2xl text-slate-600 dark:text-slate-300 font-light leading-relaxed">
                  Experience the world's first <span className="font-semibold text-blue-600">autonomous agentic HR platform</span> that transforms 
                  <span className="mx-2 px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg font-bold">₹5,00,000</span>
                  traditional operations into 
                  <span className="mx-2 px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-lg font-bold">₹50,000</span>
                  of pure AI-driven intelligence
                </p>
                
                <div className="flex items-center justify-center gap-8 text-sm text-slate-500 dark:text-slate-400">
                  <div className="flex items-center gap-2 hover:text-blue-600 transition-colors cursor-default">
                    <TbRobot className="w-5 h-5" />
                    <span>4 AI Agents</span>
                  </div>
                  <div className="flex items-center gap-2 hover:text-purple-600 transition-colors cursor-default">
                    <HiBolt className="w-5 h-5" />
                    <span>95% Faster</span>
                  </div>
                  <div className="flex items-center gap-2 hover:text-indigo-600 transition-colors cursor-default">
                    <HiSparkles className="w-5 h-5" />
                    <span>Zero Bias</span>
                  </div>
                </div>
              </div>
              
              {/* CTA Buttons */}
              <div className="hero-cta flex flex-col sm:flex-row items-center justify-center gap-6">
                <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-2xl shadow-blue-500/25 hover:shadow-3xl hover:shadow-blue-500/30 transition-all duration-300 px-8 py-4 text-lg rounded-xl hover:scale-105">
                  <a href="mailto:admin@bearsystems.co.in?subject=Experience%20the%20Future%20Now%20-%20BearSystemsHRT%20Demo%20Request" className="flex items-center gap-3">
                    <HiRocketLaunch className="w-6 h-6" />
                    Experience the Future Now
                    <HiArrowRight className="w-5 h-5" />
                  </a>
                </Button>
                
                <Button variant="outline" size="lg" className="border-2 border-slate-300 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-all duration-300 px-8 py-4 text-lg rounded-xl hover:scale-105">
                  <div className="flex items-center gap-3">
                    <HiEye className="w-6 h-6" />
                    Watch Intelligence Demo
                  </div>
                </Button>
              </div>

              {/* Trust Indicators */}
              <div className="hero-visual pt-12">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 font-medium tracking-wider uppercase">Trusted by Enterprise Leaders Worldwide</p>
                <div className="flex items-center justify-center gap-4">
                  <div className="px-6 py-3 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-transform cursor-default">
                    <div className="text-2xl font-bold text-blue-600">24hr</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">AI Response</div>
                  </div>
                  <div className="px-6 py-3 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-transform cursor-default">
                    <div className="text-2xl font-bold text-purple-600">Zero</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Human Bias</div>
                  </div>
                  <div className="px-6 py-3 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-transform cursor-default">
                    <div className="text-2xl font-bold text-indigo-600">100%</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Autonomous</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Enhanced Intelligence Showcase */}
        <section ref={statsRef} className="py-32 bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
          <div className="container px-6">
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-6">
                Intelligence that
                <span className="block font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">transforms everything</span>
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
                Revolutionary metrics that showcase the power of autonomous AI-driven HR operations
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-16 max-w-6xl mx-auto">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="text-center stat-card cursor-pointer group">
                      <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-3xl blur-xl group-hover:blur-sm transition-all duration-300"></div>
                        <div className="relative bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-all duration-300">
                          <div className="stat-number text-6xl md:text-7xl font-light text-blue-600 mb-4" data-final="95">0</div>
                          <p className="text-xl text-slate-600 dark:text-slate-300">Intelligence Boost</p>
                          <div className="w-16 h-1 bg-gradient-to-r from-blue-500 to-purple-500 mx-auto mt-4 rounded-full"></div>
                        </div>
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>1000x faster decisions with 99.2% accuracy through autonomous AI agents</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="text-center stat-card cursor-pointer group">
                      <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-3xl blur-xl group-hover:blur-sm transition-all duration-300"></div>
                        <div className="relative bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-all duration-300">
                          <div className="text-6xl md:text-7xl font-light text-purple-600 mb-4">₹2.5Cr</div>
                          <p className="text-xl text-slate-600 dark:text-slate-300">Value Generated</p>
                          <div className="w-16 h-1 bg-gradient-to-r from-purple-500 to-pink-500 mx-auto mt-4 rounded-full"></div>
                        </div>
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Cost savings + efficiency gains + risk mitigation across enterprise operations</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="text-center stat-card cursor-pointer group">
                      <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-blue-500/20 rounded-3xl blur-xl group-hover:blur-sm transition-all duration-300"></div>
                        <div className="relative bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-all duration-300">
                          <div className="stat-number text-6xl md:text-7xl font-light text-indigo-600 mb-4" data-final="60">0</div>
                          <p className="text-xl text-slate-600 dark:text-slate-300">Better Talent Match</p>
                          <div className="w-16 h-1 bg-gradient-to-r from-indigo-500 to-blue-500 mx-auto mt-4 rounded-full"></div>
                        </div>
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Superior cultural fit with zero bias detection and predictive analytics</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </section>

        {/* Interactive AI Agents Showcase */}
        <section ref={agentsRef} id="agents" className="py-32">
          <div className="container px-6">
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-6">
                Meet your
                <span className="block font-semibold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">AI workforce</span>
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
                Four specialized autonomous agents orchestrating your complete HR transformation
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
              {agents.map((agent, index) => (
                <div 
                  key={index}
                  className={`agent-card group cursor-pointer ${activeAgent === index ? 'scale-105' : ''} transition-all duration-500`}
                  onClick={() => setActiveAgent(index)}
                >
                  <div className="relative">
                    <div className={`absolute inset-0 bg-gradient-to-br ${agent.color} opacity-20 rounded-3xl blur-xl group-hover:opacity-30 transition-opacity duration-300`}></div>
                    <div className="relative bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50 hover:border-slate-300 dark:hover:border-slate-600 transition-all duration-300">
                      <div className={`w-16 h-16 mx-auto mb-6 bg-gradient-to-br ${agent.color} rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                        <agent.icon className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">{agent.name}</h3>
                      <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed mb-6">{agent.description}</p>
                      
                      {/* Interactive Capabilities */}
                      <div className="space-y-2">
                        {agent.capabilities.map((capability, capIndex) => (
                          <div key={capIndex} className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                            <span>{capability}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Active Agent Details */}
            <div className="mt-16 max-w-4xl mx-auto">
              <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50">
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                    {agents[activeAgent].name}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    From recruitment intelligence to compliance mastery, performance tracking to payroll optimization — complete autonomous HR transformation through {agents[activeAgent].name.toLowerCase()}.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Interactive Showcase Section */}
        <section ref={showcaseRef} id="showcase" className="py-32 bg-gradient-to-r from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900">
          <div className="container px-6">
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white mb-6">
                Competitive
                <span className="block font-semibold bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">Intelligence</span>
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
                While others deliver fragmented solutions, we orchestrate complete HR transformation through proprietary agentic intelligence
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
              <div className="showcase-item group">
                <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-all duration-300">
                  <div className="text-4xl font-bold text-emerald-600 mb-4">90%</div>
                  <p className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Cost Reduction</p>
                  <p className="text-sm text-slate-600 dark:text-slate-300">Infrastructure cost reduction through intelligent automation</p>
                </div>
              </div>

              <div className="showcase-item group">
                <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-all duration-300">
                  <div className="text-4xl font-bold text-blue-600 mb-4">10x</div>
                  <p className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Talent Quality</p>
                  <p className="text-sm text-slate-600 dark:text-slate-300">Enhanced talent outcomes through AI-driven selection</p>
                </div>
              </div>

              <div className="showcase-item group">
                <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-all duration-300">
                  <div className="text-4xl font-bold text-purple-600 mb-4">24/7</div>
                  <p className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Autonomous Operation</p>
                  <p className="text-sm text-slate-600 dark:text-slate-300">Complete autonomous HR intelligence platform</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Enhanced CTA */}
        <section ref={ctaRef} id="contact" className="py-32">
          <div className="container px-6 text-center">
            <div className="max-w-4xl mx-auto space-y-8 cta-content">
              <h2 className="text-4xl md:text-6xl font-light text-slate-900 dark:text-white">
                Ready to transform
                <span className="block font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">your hiring intelligence?</span>
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto mb-8">
                Join forward-thinking companies already experiencing <span className="font-semibold text-emerald-600">revolutionary cost transformation</span> and <span className="font-semibold text-blue-600">unparalleled talent outcomes</span> through our proprietary AI models
              </p>
              
              {/* Enhanced Contact Information */}
              <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 max-w-2xl mx-auto mb-8 border border-slate-200/50 dark:border-slate-700/50">
                <div className="flex items-center justify-center gap-3 mb-4">
                  <div className="p-3 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-xl">
                    <span className="text-3xl">🚀</span>
                  </div>
                  <div>
                    <p className="font-bold text-lg text-slate-900 dark:text-white">admin@bearsystems.co.in</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Autonomous AI Intelligence Response within 24 hours</p>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4 mt-6">
                  <Button size="lg" className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-xl hover:shadow-2xl transition-all duration-300 rounded-xl">
                    <a href="mailto:admin@bearsystems.co.in?subject=Experience%20the%20Future%20Now%20-%20BearSystemsHRT%20Demo%20Request" className="flex items-center gap-2">
                      <HiRocketLaunch className="w-5 h-5" />
                      Request Intelligence Demo
                    </a>
                  </Button>
                  
                  <Button variant="outline" size="lg" className="flex-1 border-2 border-slate-300 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 transition-all duration-300 rounded-xl">
                    <a href="mailto:admin@bearsystems.co.in?subject=Partnership%20Inquiry" className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-blue-600 transition-colors">
                      <BsPeopleFill className="w-5 h-5" />
                      Partnership Inquiry
                    </a>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Enhanced Footer */}
        <footer className="bg-slate-900 dark:bg-slate-950 text-white py-16">
          <div className="container px-6">
            <div className="grid md:grid-cols-4 gap-12 mb-12">
              <div className="space-y-6">
                <Link href="/" className="flex items-center space-x-3 group">
                  <div className="relative">
                    <AppLogo />
                  </div>
                  <span className="text-xl font-bold">Bear Systems <span className="text-blue-400">HRT</span></span>
                </Link>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Complete agentic HR intelligence platform powered by proprietary AI models. BearSystemsHRT© orchestrates recruitment, compliance, and workforce intelligence.
                </p>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🚀</span>
                    <span className="text-sm font-semibold text-slate-300">admin@bearsystems.co.in</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🌍</span>
                    <span className="text-sm text-slate-400">India</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-white">Platform</h3>
                <div className="space-y-3 text-sm">
                  <Link href="#agents" className="block text-slate-300 hover:text-white transition-colors">AI Agents</Link>
                  <Link href="/candidates" className="block text-slate-300 hover:text-white transition-colors">For Candidates</Link>
                  <a href="mailto:admin@bearsystems.co.in?subject=Demo%20Request" className="block text-slate-300 hover:text-white transition-colors">Request Demo</a>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-white">Company</h3>
                <div className="space-y-3 text-sm">
                  <Link href="#showcase" className="block text-slate-300 hover:text-white transition-colors">Showcase</Link>
                  <a href="https://bearsystems.co.in" target="_blank" rel="noopener noreferrer" className="block text-slate-300 hover:text-white transition-colors">BearSystems.co.in</a>
                  <Link href="#contact" className="block text-slate-300 hover:text-white transition-colors">Contact</Link>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-white">Legal</h3>
                <div className="space-y-3 text-sm">
                  <Link href="/privacy" className="block text-slate-300 hover:text-white transition-colors">Privacy</Link>
                  <Link href="/terms" className="block text-slate-300 hover:text-white transition-colors">Terms</Link>
                  <span className="block text-slate-400">Enterprise Security</span>
                </div>
              </div>
            </div>
            
            <div className="border-t border-slate-800 pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-slate-400">
              <p>&copy; 2025 Bear Systems HRT. A proud product of BearSystems.co.in.</p>
              <p>Autonomous Intelligence Response within 24 hours</p>
            </div>
          </div>
        </footer>
      </div>
    </TooltipProvider>
  );
}
