'use client';

import Link from 'next/link';
import * as React from 'react';
import { useEffect, useRef, useCallback, useMemo } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AppLogo } from '@/components/shared/app-logo';

// Lazy load heavy icons to reduce initial bundle size
import dynamic from 'next/dynamic';

// Dynamic imports for performance - only load when needed
const Icons = {
  TbBrain: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbBrain })), { ssr: false }),
  TbScale: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbScale })), { ssr: false }),
  TbTarget: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbTarget })), { ssr: false }),
  TbRocket: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbRocket })), { ssr: false }),
  TbShield: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbShield })), { ssr: false }),
  TbBulb: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbBulb })), { ssr: false }),
  TbUsers: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbUsers })), { ssr: false }),
  TbChartLine: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbChartLine })), { ssr: false }),
  TbCurrency: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbCurrencyRupee })), { ssr: false }),
  TbCheck: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbCheck })), { ssr: false }),
  TbArrowRight: dynamic(() => import('react-icons/tb').then(mod => ({ default: mod.TbArrowRight })), { ssr: false }),
  RiVerifiedBadgeFill: dynamic(() => import('react-icons/ri').then(mod => ({ default: mod.RiVerifiedBadgeFill })), { ssr: false }),
  RiStarSFill: dynamic(() => import('react-icons/ri').then(mod => ({ default: mod.RiStarSFill })), { ssr: false }),
  BsPeopleFill: dynamic(() => import('react-icons/bs').then(mod => ({ default: mod.BsPeopleFill })), { ssr: false }),
};

// Lazy load heavy components
const Table = dynamic(() => import('@/components/ui/table').then(mod => ({ 
  Table: mod.Table, 
  TableBody: mod.TableBody, 
  TableCell: mod.TableCell, 
  TableHead: mod.TableHead, 
  TableHeader: mod.TableHeader, 
  TableRow: mod.TableRow 
})), { ssr: false });

const ThemeToggle = dynamic(() => import('@/components/shared/theme-toggle').then(mod => ({ default: mod.ThemeToggle })), { ssr: false });
const Badge = dynamic(() => import('@/components/ui/badge').then(mod => ({ default: mod.Badge })), { ssr: false });
const Separator = dynamic(() => import('@/components/ui/separator').then(mod => ({ default: mod.Separator })), { ssr: false });
const HoverCard = dynamic(() => import('@/components/ui/hover-card').then(mod => ({ 
  HoverCard: mod.HoverCard, 
  HoverCardContent: mod.HoverCardContent, 
  HoverCardTrigger: mod.HoverCardTrigger 
})), { ssr: false });
const Tooltip = dynamic(() => import('@/components/ui/tooltip').then(mod => ({ 
  Tooltip: mod.Tooltip, 
  TooltipContent: mod.TooltipContent, 
  TooltipProvider: mod.TooltipProvider, 
  TooltipTrigger: mod.TooltipTrigger 
})), { ssr: false });
const Progress = dynamic(() => import('@/components/ui/progress').then(mod => ({ default: mod.Progress })), { ssr: false });

// Performance optimization: Intersection Observer hook for lazy loading visibility
const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    const currentRef = ref.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [options]);

  return [ref, isIntersecting] as const;
};

// High-performance GSAP animations with RAF optimization
const useSilkAnimations = () => {
  const heroRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);
  const featuresRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // Register GSAP ScrollTrigger with performance optimizations
    gsap.registerPlugin(ScrollTrigger);
    
    // Configure ScrollTrigger for better performance
    ScrollTrigger.config({
      autoRefreshEvents: "visibilitychange,DOMContentLoaded,load",
      refreshPriority: -1,
      fastScrollEnd: true
    });
    
    const ctx = gsap.context(() => {
      // Hero Section - Ultra smooth entrance animation
      const heroElements = heroRef.current?.querySelectorAll('.hero-animate');
      if (heroElements && heroElements.length > 0) {
        gsap.set(heroElements, { 
          opacity: 0, 
          y: 40, 
          scale: 0.98,
          transformOrigin: "center center",
          force3D: true
        });
        
        gsap.to(heroElements, {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 1.2,
          ease: "power3.out",
          stagger: 0.15,
          delay: 0.2,
          force3D: true,
          onComplete: () => {
            // Clean up transform after animation
            gsap.set(heroElements, { clearProps: "transform" });
          }
        });
      }
      
      // Stats Section - Performance optimized animation
      const statsElements = statsRef.current?.querySelectorAll('.stat-card');
      if (statsElements && statsElements.length > 0) {
        gsap.set(statsElements, { 
          opacity: 0, 
          y: 30, 
          rotationX: 8,
          transformOrigin: "center center",
          force3D: true
        });
        
        ScrollTrigger.create({
          trigger: statsRef.current,
          start: "top 85%",
          onEnter: () => {
            gsap.to(statsElements, {
              opacity: 1,
              y: 0,
              rotationX: 0,
              duration: 1.0,
              ease: "power3.out",
              stagger: 0.1,
              force3D: true,
              onComplete: () => {
                gsap.set(statsElements, { clearProps: "transform" });
              }
            });
          },
          once: true
        });
      }
      
      // Features - Optimized scroll reveal
      const featureCards = featuresRef.current?.querySelectorAll('.feature-card');
      if (featureCards && featureCards.length > 0) {
        featureCards.forEach((card: Element, index: number) => {
          gsap.set(card, { 
            opacity: 0, 
            y: 50, 
            rotationY: 8,
            transformOrigin: "center center",
            force3D: true
          });
          
          ScrollTrigger.create({
            trigger: card,
            start: "top 90%",
            onEnter: () => {
              gsap.to(card, {
                opacity: 1,
                y: 0,
                rotationY: 0,
                duration: 0.8,
                ease: "power3.out",
                delay: index * 0.05,
                force3D: true,
                onComplete: () => {
                  gsap.set(card, { clearProps: "transform" });
                }
              });
            },
            once: true
          });
        });
      }
      
      // CTA Section - Magnetic effect with performance
      const ctaElements = ctaRef.current?.querySelectorAll('.cta-animate');
      if (ctaElements && ctaElements.length > 0) {
        gsap.set(ctaElements, { 
          opacity: 0, 
          scale: 0.9,
          force3D: true
        });
        
        ScrollTrigger.create({
          trigger: ctaRef.current,
          start: "top 95%",
          onEnter: () => {
            gsap.to(ctaElements, {
              opacity: 1,
              scale: 1,
              duration: 1.0,
              ease: "back.out(1.2)",
              stagger: 0.08,
              force3D: true,
              onComplete: () => {
                gsap.set(ctaElements, { clearProps: "transform" });
              }
            });
          },
          once: true
        });
      }
    });
    
    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);
  
  return { heroRef, statsRef, featuresRef, ctaRef };
};

// Performance optimization: Memoized static data constants
const HERO_STATS = [
  { 
    value: "₹5,00,000", 
    oldValue: "₹50,000",
    label: "Traditional HR Cost vs Our AI Solution", 
    icon: Icons.TbCurrency,
    trend: "90% Cost Reduction"
  },
  { 
    value: "4", 
    label: "AI Agents Managing Complete HR Operations", 
    icon: Icons.TbBrain,
    trend: "100% Autonomous"
  },
  { 
    value: "24/7", 
    label: "Continuous Operations & Intelligence", 
    icon: Icons.TbRocket,
    trend: "Zero Downtime"
  }
];

const AI_AGENTS = [
  {
    name: "Recruitment Intelligence Agent",
    icon: Icons.TbTarget,
    description: "Advanced candidate sourcing, screening, and matching with predictive analytics for optimal hiring decisions.",
    capabilities: [
      "Intelligent candidate sourcing across multiple platforms",
      "Automated screening with behavioral analysis",
      "Predictive matching algorithms for role compatibility",
      "Real-time market intelligence and salary benchmarking"
    ]
  },
  {
    name: "Onboarding Orchestration Agent", 
    icon: Icons.TbUsers,
    description: "Seamless new hire integration with personalized workflows and automated compliance management.",
    capabilities: [
      "Personalized onboarding journey creation",
      "Automated document collection and verification", 
      "Compliance tracking and regulatory adherence",
      "Integration with existing HR systems and tools"
    ]
  },
  {
    name: "Performance Intelligence Agent",
    icon: Icons.TbChartLine, 
    description: "Continuous performance monitoring with predictive insights and development recommendations.",
    capabilities: [
      "Real-time performance analytics and insights",
      "Predictive career path recommendations",
      "Automated goal setting and progress tracking",
      "360-degree feedback orchestration"
    ]
  },
  {
    name: "Payroll Optimization Agent",
    icon: Icons.TbScale,
    description: "Intelligent payroll processing with compliance automation and cost optimization strategies.",
    capabilities: [
      "Automated payroll processing and calculations",
      "Tax compliance and regulatory updates",
      "Benefits optimization and cost analysis", 
      "Fraud detection and audit trail maintenance"
    ]
  }
];

const COMPETITIVE_ANALYSIS = [
  { 
    feature: "Setup Time", 
    traditional: "6-12 months", 
    ours: "2-4 weeks",
    advantage: "10x Faster"
  },
  { 
    feature: "Monthly Cost", 
    traditional: "₹5,00,000+", 
    ours: "₹50,000",
    advantage: "90% Savings"
  },
  { 
    feature: "Error Rate", 
    traditional: "15-20%", 
    ours: "<1%",
    advantage: "20x More Accurate"
  },
  { 
    feature: "Compliance Updates", 
    traditional: "Manual/Quarterly", 
    ours: "Automatic/Real-time",
    advantage: "Always Current"
  },
  { 
    feature: "Scalability", 
    traditional: "Linear Cost Growth", 
    ours: "Flat Rate Scaling",
    advantage: "Unlimited Growth"
  }
];

const TRANSFORMATION_BENEFITS = [
  {
    title: "Recruitment Revolution",
    description: "From recruitment to performance intelligence, payroll optimization to compliance mastery - BearSystemsHRT© orchestrates every aspect of HR operations through seamless agentic intelligence.",
    features: [
      "Integrated recruitment, onboarding, and performance intelligence tracking",
      "Autonomous payroll optimization and benefits intelligence management",
      "Predictive analytics for workforce planning and talent retention",
      "Real-time compliance monitoring across all regulatory frameworks"
    ],
    metrics: [
      "95% faster candidate matching with AI-powered screening algorithms", 
      "87% reduction in onboarding time through automated workflow orchestration",
      "78% improvement in employee retention via predictive analytics insights",
      "99.9% compliance accuracy with real-time regulatory intelligence updates",
      "Compressed storage reduces infrastructure costs by 80% through AI optimization",
      "Seamless integration with 200+ existing HR platforms and enterprise systems"
    ]
  }
];

// Performance optimization: Static data constants
const CTA_DATA = {
  title: "Transform Your HR Operations Today",
  subtitle: "Join the agentic revolution and experience the future of human resources.",
  description: "Ready to revolutionize your HR operations? Our AI agents are standing by to transform your workforce management.",
  buttonText: "Get Started Now",
  features: [
    "✓ 30-day free trial",
    "✓ White-glove onboarding",
    "✓ 24/7 expert support"
  ]
};

export default function HomePage() {
  const { heroRef, statsRef, featuresRef: gsapFeaturesRef, ctaRef } = useSilkAnimations();
  
  // Performance optimization: Intersection observers for lazy loading heavy sections
  const [featuresRef, featuresVisible] = useIntersectionObserver({ threshold: 0.1 });
  const [comparisonRef, comparisonVisible] = useIntersectionObserver({ threshold: 0.1 });
  const [benefitsRef, benefitsVisible] = useIntersectionObserver({ threshold: 0.1 });

  // Memoized components for performance
  const MemoizedStatsSection = useMemo(() => (
    <section ref={statsRef} className="py-16 bg-white dark:bg-slate-900">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {HERO_STATS.map((stat, index) => {
            const IconComponent = stat.icon;
            return (
              <Card key={index} className="stat-card text-center border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                <CardContent className="pt-6">
                  <div className="flex justify-center mb-4">
                    <IconComponent className="h-12 w-12 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="space-y-2">
                    <div className="text-3xl font-bold text-slate-900 dark:text-white">
                      {stat.value}
                      {stat.oldValue && (
                        <span className="text-lg line-through text-slate-400 ml-2">
                          {stat.oldValue}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-600 dark:text-slate-300 text-sm">{stat.label}</p>
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                      {stat.trend}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  ), []);

  return (
    <div className="min-h-screen bg-white dark:bg-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <AppLogo />
            <span className="text-xl font-bold text-slate-900 dark:text-white">
              BearSystemsHRT©
            </span>
          </div>
          <nav className="hidden md:flex items-center space-x-6">
            <Link href="/candidates" className="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition-colors">
              Candidates
            </Link>
            <Link href="/privacy" className="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition-colors">
              Terms
            </Link>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section ref={heroRef} className="py-20 px-4 bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
        <div className="container mx-auto text-center">
          <div className="hero-animate mb-6">
            <h1 className="text-4xl md:text-6xl font-bold text-slate-900 dark:text-white mb-6">
              Agentic AI Platform for
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"> Complete HR Transformation</span>
            </h1>
          </div>
          
          <div className="hero-animate mb-8">
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
              Four specialized AI agents working 24/7 to revolutionize your entire HR operations. 
              From recruitment to payroll, compliance to performance - all automated, intelligent, and cost-effective.
            </p>
          </div>
          
          <div className="hero-animate flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white">
              <Link href="/candidates" className="flex items-center">
                Start Free Trial
                <Icons.TbArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline">
              Watch Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      {MemoizedStatsSection}

      {/* AI Agents Showcase */}
      <section ref={featuresRef} className="py-20 bg-slate-50 dark:bg-slate-800">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Meet Your AI Workforce
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300">
              Four specialized agents handling every aspect of HR operations
            </p>
          </div>
          
          {featuresVisible && (
            <div ref={gsapFeaturesRef} className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {AI_AGENTS.map((agent, index) => {
                const IconComponent = agent.icon;
                return (
                  <Card key={index} className="feature-card border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                    <CardHeader>
                      <div className="flex items-center space-x-4">
                        <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900">
                          <IconComponent className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                        </div>
                        <CardTitle className="text-xl">{agent.name}</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300 mb-4">{agent.description}</p>
                      <ul className="space-y-2">
                        {agent.capabilities.map((capability, capIndex) => (
                          <li key={capIndex} className="flex items-start space-x-2 text-sm">
                            <Icons.TbCheck className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="text-slate-600 dark:text-slate-300">{capability}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Competitive Analysis */}
      <section ref={comparisonRef} className="py-20 bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Traditional HR vs Agentic AI
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300">
              See why leading companies are making the switch
            </p>
          </div>
          
          {comparisonVisible && (
            <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
              <Table.Table>
                <Table.TableHeader>
                  <Table.TableRow>
                    <Table.TableHead className="w-1/4">Feature</Table.TableHead>
                    <Table.TableHead className="w-1/4">Traditional HR</Table.TableHead>
                    <Table.TableHead className="w-1/4">BearSystemsHRT©</Table.TableHead>
                    <Table.TableHead className="w-1/4">Advantage</Table.TableHead>
                  </Table.TableRow>
                </Table.TableHeader>
                <Table.TableBody>
                  {COMPETITIVE_ANALYSIS.map((row, index) => (
                    <Table.TableRow key={index}>
                      <Table.TableCell className="font-medium">{row.feature}</Table.TableCell>
                      <Table.TableCell className="text-red-600 dark:text-red-400">{row.traditional}</Table.TableCell>
                      <Table.TableCell className="text-green-600 dark:text-green-400 font-semibold">{row.ours}</Table.TableCell>
                      <Table.TableCell>
                        <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                          {row.advantage}
                        </Badge>
                      </Table.TableCell>
                    </Table.TableRow>
                  ))}
                </Table.TableBody>
              </Table.Table>
            </div>
          )}
        </div>
      </section>

      {/* Transformation Benefits */}
      <section ref={benefitsRef} className="py-20 bg-slate-50 dark:bg-slate-800">
        <div className="container mx-auto px-4">
          {benefitsVisible && TRANSFORMATION_BENEFITS.map((benefit, index) => (
            <div key={index} className="max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
                  {benefit.title}
                </h2>
                <p className="text-xl text-slate-600 dark:text-slate-300">
                  {benefit.description}
                </p>
              </div>
              
              <div className="grid md:grid-cols-2 gap-8">
                <Card className="border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-xl text-slate-900 dark:text-white">Core Capabilities</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {benefit.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-start space-x-3">
                          <Icons.TbCheck className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-slate-600 dark:text-slate-300">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
                
                <Card className="border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-xl text-slate-900 dark:text-white">Performance Metrics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {benefit.metrics.map((metric, metricIndex) => (
                        <li key={metricIndex} className="flex items-start space-x-3">
                          <Icons.RiStarSFill className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <span className="text-slate-600 dark:text-slate-300">{metric}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section ref={ctaRef} className="py-20 bg-gradient-to-br from-blue-600 to-purple-600">
        <div className="container mx-auto px-4 text-center">
          <div className="cta-animate mb-6">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {CTA_DATA.title}
            </h2>
            <p className="text-xl text-blue-100 mb-2">
              {CTA_DATA.subtitle}
            </p>
            <p className="text-blue-100 max-w-2xl mx-auto">
              {CTA_DATA.description}
            </p>
          </div>
          
          <div className="cta-animate mb-8">
            <div className="flex flex-wrap justify-center gap-4 mb-8">
              {CTA_DATA.features.map((feature, index) => (
                <span key={index} className="text-blue-100 text-sm">
                  {feature}
                </span>
              ))}
            </div>
          </div>
          
          <div className="cta-animate">
            <Button size="lg" className="bg-white text-blue-600 hover:bg-blue-50">
              <Link href="/candidates" className="flex items-center">
                {CTA_DATA.buttonText}
                <Icons.TbArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <AppLogo />
                <span className="text-lg font-bold">BearSystemsHRT©</span>
              </div>
              <p className="text-slate-400 text-sm">
                Revolutionizing HR operations through agentic AI intelligence.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Platform</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link href="/candidates" className="hover:text-white transition-colors">Candidates</Link></li>
                <li><a href="#agents" className="hover:text-white transition-colors">AI Agents</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#demo" className="hover:text-white transition-colors">Demo</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#about" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#contact" className="hover:text-white transition-colors">Contact</a></li>
                <li><a href="#careers" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#blog" className="hover:text-white transition-colors">Blog</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Legal</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
                <li><a href="#security" className="hover:text-white transition-colors">Security</a></li>
                <li><a href="#compliance" className="hover:text-white transition-colors">Compliance</a></li>
              </ul>
            </div>
          </div>
          
          <Separator className="my-8 bg-slate-700" />
          
          <div className="flex flex-col md:flex-row items-center justify-between text-sm text-slate-400">
            <p>&copy; 2024 BearSystemsHRT©. All rights reserved.</p>
            <p>Powered by Advanced Agentic AI Intelligence</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
