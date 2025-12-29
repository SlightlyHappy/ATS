
'use client';
import Link from 'next/link';
import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AppLogo } from '@/components/shared/app-logo';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { Badge } from '@/components/ui/badge';

// Performance optimization: Intersection Observer hook for lazy loading visibility
const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = React.useState(false);
  const [hasIntersected, setHasIntersected] = React.useState(false);
  const targetRef = React.useRef(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
      if (entry.isIntersecting && !hasIntersected) {
        setHasIntersected(true);
      }
    }, options);

    if (targetRef.current) {
      observer.observe(targetRef.current);
    }

    return () => observer.disconnect();
  }, [options, hasIntersected]);

  return [targetRef, isIntersecting, hasIntersected];
};

// GSAP Silk Animation Hooks for Premium Landing Page
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
      autoRefreshEvents: "visibilitychange,DOMContentLoaded,load"
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
            // Clean up transform after animation for better performance
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

// Performance optimization: Static data constants (will be memoized inside component)
const agentFeatures = [
  {
    title: 'Technical Intelligence Agent',
    status: 'Active',
    description: 'Comprehensive analysis of programming languages, frameworks, certifications with intelligent skill trend assessment',
    capabilities: [
        'Advanced skill proficiency evaluation',
        'Technical certification validation',
        'Technology trend analysis',
        'Project complexity assessment'
    ]
  },
  {
    title: 'Experience Intelligence Evaluator',
    status: 'Active', 
    description: 'Professional validation of career trajectories, progression analysis, and leadership potential evaluation',
    capabilities: [
        'Career trajectory modeling',
        'Achievement analysis',
        'Leadership potential assessment',
        'Industry experience mapping'
    ]
  },
  {
    title: 'Cultural Intelligence Analyzer',
    status: 'Active',
    description: 'Professional assessment of communication patterns, soft skills analysis, and team compatibility evaluation',
    capabilities: [
        'Communication pattern analysis',
        'Soft skill evaluation',
        'Team compatibility assessment',
        'Cultural alignment analysis'
    ]
  },
  {
    title: 'Legal Compliance Guardian',
    status: 'Active',
    description: 'Comprehensive bias detection, Indian labor law compliance monitoring, and audit trail management',
    capabilities: [
        'Bias detection and mitigation',
        'Legal compliance verification',
        'Fairness assessment protocols',
        'Audit trail documentation'
    ]
  }
];

// Performance optimization: Static data constants
const learningFeatures = [
  {
    icon: <HiAcademicCap className="h-8 w-8 text-primary" />,
    title: 'Agentic Career Pathway Intelligence',
    description: 'AI-powered learning pathways tailored to each candidate\'s unique career aspirations and market demands',
    features: [
      'Personalized skill development roadmaps based on industry trends',
      'Real-time market demand analysis for skill prioritization',
      'Dynamic learning content recommendations from top-tier sources',
      'Progress tracking with intelligent milestone predictions'
    ]
  },
  {
    icon: <BsPeopleFill className="h-8 w-8 text-primary" />,
    title: 'Peer Comparison Intelligence Engine',
    description: 'Advanced agentic analysis comparing candidates with industry peers for competitive positioning',
    features: [
      'Anonymous peer benchmarking across similar roles and experience levels',
      'Skill gap identification through intelligent peer analysis',
      'Competitive positioning insights for career advancement',
      'Industry-specific competency mapping and recommendations'
    ]
  },
  {
    icon: <HiArrowTrendingUp className="h-8 w-8 text-primary" />,
    title: 'Market Trend Guidance System',
    description: 'Real-time career guidance powered by latest market trends and emerging skill demands',
    features: [
      'Emerging skill trend detection from global job markets',
      'Industry shift predictions with career pivot recommendations',
      'Salary trend analysis for informed career decisions',
      'Future-ready skill identification and development paths'
    ]
  }
];

// Performance optimization: Static data constants  
const complianceFeatures = [
  {
    icon: <TbScale className="h-8 w-8 text-primary" />,
    title: 'Autonomous Legal Document Intelligence',
    description: 'AI systems continuously monitor and update legal compliance based on latest regulatory changes',
    features: [
      'Real-time scraping of latest labor law updates from government sources',
      'Automatic policy updates based on regulatory changes',
      'Compliance risk assessment for all HR processes',
      'Audit-ready documentation with legal traceability'
    ]
  },
  {
    icon: <RiVerifiedBadgeFill className="h-8 w-8 text-primary" />,
    title: 'In-House Legal AI Training Engine',
    description: 'Proprietary AI models trained specifically on Indian labor laws and compliance requirements',
    features: [
      'Specialized training on Indian Labor Law Code 2020',
      'State-specific compliance requirement mapping',
      'Industry-specific regulatory guidance integration',
      'Continuous learning from legal precedents and updates'
    ]
  },
  {
    title: 'Proactive Compliance Monitoring',
    description: 'Intelligent monitoring systems that prevent compliance violations before they occur',
    features: [
      'Predictive compliance risk alerts and recommendations',
      'Automated compliance checking for all HR decisions',
      'Real-time legal validation of policies and procedures',
      'Comprehensive audit trails for regulatory inspections'
    ]
  }
];

// Performance optimization: Static data constants
const techFeatures = [
    {
        title: "Proprietary Recruitment Intelligence Constellation",
        value: "Engineered from Inception",
        description: "Our flagship agentic recruitment model architected from the ground up on 500K+ Indian hiring scenarios with advanced bias mitigation and cultural intelligence understanding.",
        points: [
            "99.2% bias-free intelligent hiring decisions with real-time cognitive alerts",
            "Deep cultural intelligence understanding of Indian career patterns and contexts",
            "Advanced skill synthesis and growth potential prediction algorithms",
            "Continuous learning from organizational hiring intelligence outcomes"
        ]
    },
    {
        title: "Legal Compliance Intelligence Engine",
        value: "100% Autonomous Compliance",
        description: "Proprietary legal intelligence model with comprehensive Indian Labor Law neural database, autonomous compliance orchestration, and real-time regulatory intelligence updates.",
        points: [
            "Built-in Indian Labor Law neural database with 2024 intelligence updates",
            "Autonomous audit trails for every HR intelligence decision",
            "Real-time compliance verification across all HR cognitive functions",
            "Protection against discrimination and legal violations through AI vigilance"
        ]
    },
    {
        title: "End-to-End HR Intelligence Orchestration",
        value: "Complete Agentic Solution",
        description: "From recruitment to performance intelligence, payroll optimization to compliance mastery - BearSystemsHRT© orchestrates every aspect of HR operations through seamless agentic intelligence.",
        points: [
            "Integrated recruitment, onboarding, and performance intelligence tracking",
            "Autonomous payroll optimization and benefits intelligence management",
            "Real-time employee engagement and satisfaction intelligence monitoring",
            "Comprehensive analytics and predictive HR intelligence insights"
        ]
    },
    {
        title: "Enterprise-Grade Security & Intelligent Scale",
        value: "Military-Grade Intelligence",
        description: "AES-256 encryption, compressed storage architecture, and zero data leak guarantee with enterprise-scale agentic deployment capabilities.",
        points: [
            "AES-256 encryption for all sensitive HR intelligence data",
            "Compressed storage reduces infrastructure costs by 80% through AI optimization",
            "Zero-trust security architecture with SOC 2 compliance intelligence",
            "Seamless integration with existing HRMS and payroll systems through agentic connectors"
        ]
    }
];

// Performance optimization: Static data constants
const competitiveData = [
    { feature: "HR Coverage", traditional: "Point solutions only", basic: "Limited modules", our: "Complete end-to-end agentic HR intelligence" },
    { feature: "AI Models", traditional: "Manual keyword matching", basic: "Single AI model scanning", our: "Proprietary agentic recruitment + legal intelligence models" },
    { feature: "Training Data", traditional: "Generic global data", basic: "Basic training sets", our: "500K+ Indian hiring scenarios with agentic learning" },
    { feature: "Legal Compliance", traditional: "Manual compliance checking", basic: "Generic global compliance", our: "Built-in Indian labor law agentic engine" },
    { feature: "Bias Detection", traditional: "Manual review (prone to bias)", basic: "Basic sentiment analysis", our: "99.2% bias-free proprietary agentic model" },
    { feature: "Data Security", traditional: "Basic password protection", basic: "Standard encryption", our: "AES-256 + compressed agentic storage" },
    { feature: "Platform Type", traditional: "Separate HR tools", basic: "Basic integration", our: "Unified autonomous agentic intelligence system" }
];


export default function Home() {
  const [currentYear, setCurrentYear] = React.useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  
  React.useEffect(() => {
    setCurrentYear(new Date().getFullYear());
  }, []);
  
  // GSAP Silk Animations Hook
  const { heroRef, statsRef, featuresRef: gsapFeaturesRef, ctaRef } = useSilkAnimations();
  
  // Performance optimization: Intersection observers for lazy loading heavy sections
  const [featuresRef, , hasFeaturesIntersected] = useIntersectionObserver({
    rootMargin: '100px',
    threshold: 0.1
  });
  const [learningRef, , hasLearningIntersected] = useIntersectionObserver({
    rootMargin: '100px',
    threshold: 0.1
  });
  const [complianceRef, , hasComplianceIntersected] = useIntersectionObserver({
    rootMargin: '100px', 
    threshold: 0.1
  });
  const [aboutRef, , hasAboutIntersected] = useIntersectionObserver({
    rootMargin: '100px',
    threshold: 0.1
  });
  
  const handleMobileMenuClick = useCallback(() => {
    setMobileMenuOpen(false);
  }, []);
  
  // Performance optimization: Memoize expensive calculations
  const memoizedStats = useMemo(() => [
    { 
      number: "75%", 
      unit: "Faster Hiring",
      description: "Streamlined recruitment for Indian market",
      highlight: "Smart AI Analysis"
    },
    { 
      number: "90%", 
      unit: "Accuracy",
      description: "Precise candidate-role matching",
      highlight: "AI-Powered Intelligence"
    },
    { 
      number: "100%", 
      unit: "Compliance",
      description: "Indian Labor Law adherence",
      highlight: "Built-in Legal Intelligence"
    }
  ], []);
  
  const memoizedFeatures = useMemo(() => [
    {
      title: "Recruitment Intelligence Agent",
      description: "Advanced candidate sourcing, screening, and matching with predictive analytics for optimal hiring decisions."
    },
    {
      title: "Onboarding Orchestration Agent", 
      description: "Seamless new hire integration with personalized workflows and automated compliance management."
    },
    {
      title: "Performance Intelligence Agent",
      description: "Continuous performance monitoring with predictive insights and development recommendations."
    },
    {
      title: "Payroll Optimization Agent",
      description: "Intelligent payroll processing with compliance automation and cost optimization strategies."
    }
  ], []);

  return (
    <TooltipProvider>
      <div className="flex min-h-screen flex-col text-foreground relative overflow-hidden"
           itemScope 
           itemType="https://schema.org/SoftwareApplication">
        
        {/* Unified Luxurious Animated Background */}
        <div className="unified-luxury-bg">
          {/* Animated gradient overlay */}
          <div className="luxury-gradient-overlay"></div>
          
          {/* Floating orbs */}
          <div className="luxury-orb luxury-orb-1"></div>
          <div className="luxury-orb luxury-orb-2"></div>
          <div className="luxury-orb luxury-orb-3"></div>
          
          {/* Mesh gradient pattern */}
          <div className="luxury-mesh"></div>
          
          {/* Animated particles */}
          <div className="luxury-particles">
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
            <div className="luxury-particle"></div>
          </div>
          
          {/* Grid pattern overlay */}
          <div className="luxury-grid"></div>
        </div>
        
        <meta name="description" content="BearSystemsHRT© - Advanced AI-Powered Human Resources Platform. Transform HR operations with intelligent automation for recruitment, compliance, and workforce management. Enterprise-grade HR technology solutions." />
        <meta name="keywords" content="AI HR Platform, Human Resources, AI Recruitment, HR Technology, Intelligent Automation, Workforce Intelligence, HR Compliance, Recruitment Solutions, Enterprise HR Software, HR Analytics, Talent Management, HR Innovation" />
        
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center">
            <Link href="/" className="mr-6 flex items-center space-x-2">
              <AppLogo />
              <span className="font-bold font-headline text-sm sm:text-base">Bear Systems <span className="text-primary">HRT</span></span>
            </Link>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex flex-1 items-center space-x-6 text-sm font-medium">
               <Link href="#features" className="text-muted-foreground transition-colors hover:text-foreground">AI Technology</Link>
               <Link href="#learning" className="text-muted-foreground transition-colors hover:text-foreground">Learning & Development</Link>
               <Link href="#compliance" className="text-muted-foreground transition-colors hover:text-foreground">Legal Compliance</Link>
               <Link href="#about" className="text-muted-foreground transition-colors hover:text-foreground">About Us</Link>
               <Link href="#contact" className="text-muted-foreground transition-colors hover:text-foreground">Contact</Link>
            </nav>
            
            <div className="flex items-center space-x-2">
              <ThemeToggle />
              <Button asChild variant="outline" className="hidden sm:inline-flex">
                <Link href="/admin/login">Login</Link>
              </Button>
              <Button asChild className="hidden sm:inline-flex">
                <Link href="/candidates">For Candidates</Link>
              </Button>
              
              {/* Mobile Menu Button */}
              <Button
                variant="ghost"
                size="sm"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <HiXMark className="h-5 w-5" /> : <HiBars3 className="h-5 w-5" />}
              </Button>
            </div>
          </div>
          
          {/* Mobile Navigation Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t bg-background/95 backdrop-blur">
              <nav className="container py-4 space-y-2">
                <Link 
                  href="#features" 
                  className="block py-2 px-4 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                  onClick={handleMobileMenuClick}
                >
                  AI Technology
                </Link>
                <Link 
                  href="#learning" 
                  className="block py-2 px-4 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                  onClick={handleMobileMenuClick}
                >
                  Learning & Development
                </Link>
                <Link 
                  href="#compliance" 
                  className="block py-2 px-4 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                  onClick={handleMobileMenuClick}
                >
                  Legal Compliance
                </Link>
                <Link 
                  href="#about" 
                  className="block py-2 px-4 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                  onClick={handleMobileMenuClick}
                >
                  About Us
                </Link>
                <Link 
                  href="#contact" 
                  className="block py-2 px-4 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                  onClick={handleMobileMenuClick}
                >
                  Contact
                </Link>
                <div className="pt-2 space-y-2">
                  <Button asChild variant="outline" className="w-full">
                    <Link href="/admin/login">Login</Link>
                  </Button>
                  <Button asChild className="w-full">
                    <Link href="/candidates">For Candidates</Link>
                  </Button>
                </div>
              </nav>
            </div>
          )}
        </header>
      <main className="flex-1">
        {/* Ultra-Luxury Hero Section - Unified Background */}
        <section ref={heroRef} className="relative grid items-center gap-4 sm:gap-6 md:gap-8 lg:gap-12 py-8 sm:py-12 md:py-16 lg:py-24 xl:py-32 hero-mobile sm:ipad-hero md:ipad-landscape-hero w-full overflow-hidden">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 w-full max-w-full">
            
            <div className="flex flex-col items-center space-y-6 sm:space-y-8 md:space-y-10 lg:space-y-12 text-center relative max-w-5xl mx-auto w-full">
              {/* Premium announcement badge - FIXED Mobile Layout */}
              <div className="relative group w-full max-w-full px-4 sm:px-0 hero-animate">
                <Badge variant="secondary" className="mobile-badge relative px-3 py-2 text-xs sm:text-sm font-medium bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:scale-105 transition-all duration-500 animate-shimmer w-full sm:w-auto max-w-full">
                  <div className="flex items-center justify-center gap-2 flex-wrap text-center">
                    <span className="text-gradient-luxury text-xs leading-tight max-w-full overflow-hidden text-ellipsis">Advanced AI HR Platform - Built for India</span>
                  </div>
                </Badge>
              </div>
              
              {/* Ultra-premium headline - Viewport Constrained */}
              <div className="space-y-3 sm:space-y-4 md:space-y-6 lg:space-y-8 relative w-full max-w-full hero-animate">
                <div className="relative overflow-hidden">
                  <h1 className="hero-title text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl 2xl:text-7xl font-black leading-[0.95] sm:leading-[0.9] tracking-tight font-headline relative px-2 sm:px-0 text-wrap-mobile w-full"
                      itemProp="name">
                    <span className="block text-gradient-luxury">Enterprise AI-Powered</span>
                    <span className="block text-gradient-premium mt-0.5 sm:mt-1 md:mt-2">Talent Intelligence</span>
                    <span className="block text-gradient-luxury mt-0.5 sm:mt-1 md:mt-2">Platform</span>
                    <span className="block text-slate-600 dark:text-slate-400 mt-0.5 sm:mt-1 md:mt-2 text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl 2xl:text-6xl font-light">Sub-60 Second Analysis</span>
                  </h1>
                  
                  {/* Luxury decorative elements - Hidden on mobile for performance and space */}
                  <div className="hidden lg:block absolute -top-8 -left-8 w-24 h-24 border border-blue-100/30 dark:border-blue-800/30 rounded-full animate-float opacity-60" />
                  <div className="hidden lg:block absolute -bottom-4 -right-4 w-16 h-16 border border-purple-100/40 dark:border-purple-800/40 rounded-full animate-float-delayed opacity-40" />
                  <div className="hidden xl:block absolute top-1/2 -right-12 w-2 h-32 bg-gradient-to-b from-transparent via-blue-200/20 dark:via-blue-800/20 to-transparent blur-sm" />
                </div>
              </div>
              
              {/* Premium description with interactive elements - Mobile Responsive */}
              <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6 hero-animate">
                <p className="text-lg sm:text-xl md:text-2xl text-slate-600 dark:text-slate-300 leading-relaxed font-light px-4 sm:px-0" itemProp="description">
                  Revolutionary AI-powered talent intelligence platform engineered for Indian enterprises and regulatory excellence.
                </p>
                
                <div className="hero-glass p-4 sm:p-6 rounded-xl sm:rounded-2xl max-w-3xl mx-auto">
                  <p className="text-base sm:text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                    Witness autonomous AI agents transform your{' '}
                    <HoverCard>
                      <HoverCardTrigger asChild>
                        <span className="font-semibold text-red-600 dark:text-red-400 cursor-pointer hover:underline decoration-red-300 px-1 sm:px-2 py-1 bg-red-50/50 dark:bg-red-950/20 rounded-lg transition-all duration-300 hover:bg-red-100/50 dark:hover:bg-red-900/30">
                          ₹5,00,000 HR operations
                        </span>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-80 sm:w-96 glass-card">
                        <div className="space-y-4">
                          <h4 className="text-base sm:text-lg font-semibold flex items-center gap-2">
                            <HiArrowTrendingUp className="h-4 w-4 sm:h-5 sm:w-5 text-red-500" />
                            Traditional HR Operational Costs
                          </h4>
                          <div className="space-y-3 text-xs sm:text-sm text-muted-foreground">
                            <div className="flex justify-between items-center">
                              <span>Recruitment & Hiring</span>
                              <span className="font-medium">₹2,50,000</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span>Compliance Management</span>
                              <span className="font-medium">₹1,50,000</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span>Performance Tracking</span>
                              <span className="font-medium">₹1,00,000</span>
                            </div>
                            <Separator />
                            <div className="flex justify-between items-center font-semibold text-red-600">
                              <span>Total Annual Cost</span>
                              <span>₹5,00,000</span>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                              <span>Efficiency Rating</span>
                              <span className="text-red-500">30%</span>
                            </div>
                            <Progress value={30} className="h-2 bg-red-100 dark:bg-red-950" />
                          </div>
                        </div>
                      </HoverCardContent>
                    </HoverCard>
                    {' '}into{' '}
                    <HoverCard>
                      <HoverCardTrigger asChild>
                        <span className="font-semibold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline decoration-emerald-300 px-2 py-1 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-lg transition-all duration-300 hover:bg-emerald-100/50 dark:hover:bg-emerald-900/30">
                          ₹50,000 of pure AI-driven intelligence
                        </span>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-96 glass-card">
                        <div className="space-y-4">
                          <h4 className="text-lg font-semibold flex items-center gap-2">
                            <TbBrain className="h-5 w-5 text-emerald-500" />
                            Agentic AI Efficiency Revolution
                          </h4>
                          <div className="space-y-3 text-sm text-muted-foreground">
                            <div className="flex justify-between items-center">
                              <span>AI Platform Subscription</span>
                              <span className="font-medium">₹30,000</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span>Maintenance & Updates</span>
                              <span className="font-medium">₹15,000</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span>Support & Training</span>
                              <span className="font-medium">₹5,000</span>
                            </div>
                            <Separator />
                            <div className="flex justify-between items-center font-semibold text-emerald-600">
                              <span>Total Annual Cost</span>
                              <span>₹50,000</span>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                              <span>Efficiency Rating</span>
                              <span className="text-emerald-500">95%</span>
                            </div>
                            <Progress value={95} className="h-2 bg-emerald-100 dark:bg-emerald-950" />
                          </div>
                          <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/20 p-2 rounded-lg">
                            <span className="w-2 h-2 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full"></span>
                            <span className="font-medium">90% cost reduction • 10x ROI in 6 months</span>
                          </div>
                        </div>
                      </HoverCardContent>
                    </HoverCard>
                  </p>
                </div>
                
                <div className="glass-card p-4 rounded-xl max-w-2xl mx-auto">
                  <p className="text-base text-slate-600 dark:text-slate-400 leading-relaxed">
                    Pioneering the future with our proprietary{' '}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="font-medium text-blue-600 dark:text-blue-400 underline decoration-blue-300/50 cursor-help hover:decoration-blue-400 transition-colors duration-300">
                          Recruitment Intelligence Model
                        </span>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="glass-card">
                        <p className="text-sm">Advanced AI trained on extensive Indian hiring patterns</p>
                      </TooltipContent>
                    </Tooltip>
                    {' '}and{' '}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="font-medium text-purple-600 dark:text-purple-400 underline decoration-purple-300/50 cursor-help hover:decoration-purple-400 transition-colors duration-300">
                          Legal Compliance Engine
                        </span>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="glass-card">
                        <p className="text-sm">Intelligent Indian labor law compliance and monitoring</p>
                      </TooltipContent>
                    </Tooltip>
                    {' '}— advanced AI innovations engineered specifically for Indian enterprises and regulatory excellence.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Ultra-premium CTA buttons - FIXED Mobile Layout */}
            <div className="button-group-mobile flex flex-col gap-3 pt-4 w-full max-w-full hero-animate">
              <div className="relative group w-full cta-animate">
                <Button asChild size="lg" className="relative btn-mobile bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 rounded-xl shadow-lg transition-all duration-300 group font-medium">
                  <a href="mailto:admin@bearsystems.co.in?subject=Experience%20the%20Future%20Now%20-%20BearSystemsHRT%20Demo%20Request" className="w-full flex items-center justify-center gap-2">
                    <span className="truncate">Get Enterprise Demo</span>
                    <HiArrowRight className="h-4 w-4 flex-shrink-0" />
                  </a>
                </Button>
              </div>
              
              <Button asChild size="lg" variant="outline" className="btn-mobile glass-card hover:bg-white/10 dark:hover:bg-black/10 border-slate-200/30 dark:border-slate-700/30 transition-all duration-300 group font-medium rounded-xl cta-animate">
                <Link href="#features" className="w-full flex items-center justify-center gap-2">
                  <span className="truncate">Explore AI Intelligence</span>
                </Link>
              </Button>
            </div>
            
            {/* Corporate trust indicators */}
            <div className="pt-8">
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 font-medium tracking-wider uppercase">Enterprise HR Technology Platform</p>
              <div className="flex items-center justify-center gap-8 opacity-60">
                <span className="text-xs text-slate-500">Enterprise Security</span>
                <div className="w-2 h-2 bg-slate-400 rounded-full"></div>
                <span className="text-xs text-slate-500">AI Technology</span>
                <div className="w-2 h-2 bg-slate-400 rounded-full"></div>
                <span className="text-xs text-slate-500">Indian Market</span>
              </div>
            </div>
          </div>
          
          {/* Ultra-Premium Stats Section - Enhanced Mobile & iPad */}
          <div ref={statsRef} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8 mt-12 sm:mt-16 lg:mt-20 px-4 sm:px-0 cards-mobile sm:ipad-cards lg:ipad-landscape-grid">
            <HoverCard>
              <HoverCardTrigger asChild>
                <div className="relative group cursor-pointer stat-card">
                  <div className="relative glass-card text-center p-8 rounded-3xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-700 border-slate-200/30 dark:border-slate-700/30 overflow-hidden">
                    
                    <div className="relative z-10">
                      <div className="relative mb-4">
                        <div className="text-6xl font-black text-gradient-premium mb-3 group-hover:scale-110 transition-transform duration-500">95%</div>
                        <div className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-500">
                          <div className="w-4 h-4 bg-gradient-to-br from-slate-400 to-slate-500 rounded-full animate-luxury-pulse"></div>
                        </div>
                      </div>
                      <div className="font-medium text-slate-600 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100 transition-colors duration-500 mb-4">
                        Agentic Intelligence Boost
                      </div>
                      <div className="w-full bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-950 dark:to-purple-950 rounded-full h-1 opacity-0 group-hover:opacity-100 transition-all duration-700">
                        <div className="h-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full transition-all duration-1000 group-hover:w-[95%] w-0"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </HoverCardTrigger>
              <HoverCardContent className="w-96 glass-card border-slate-200/30 dark:border-slate-700/30">
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold flex items-center gap-2">
                    <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-lg">
                      <HiArrowTrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    Intelligence Amplification Analysis
                  </h4>
                  <div className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Decision Speed</span>
                      <span className="font-semibold text-blue-600">1000x faster</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Accuracy Improvement</span>
                      <span className="font-semibold text-purple-600">99.2%</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Human Bias Reduction</span>
                      <span className="font-semibold text-emerald-600">100%</span>
                    </div>
                  </div>
                  <div className="p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30 rounded-xl border border-blue-100 dark:border-blue-800/30">
                    <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                      Our agentic AI systems boost organizational intelligence through autonomous decision-making, 
                      predictive analytics, and real-time optimization across all HR processes.
                    </p>
                  </div>
                </div>
              </HoverCardContent>
            </HoverCard>

            <HoverCard>
              <HoverCardTrigger asChild>
                <div className="relative group cursor-pointer stat-card">
                  <div className="relative glass-card text-center p-8 rounded-3xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-700 border-slate-200/30 dark:border-slate-700/30 overflow-hidden">
                    <div className="relative z-10">
                      <div className="relative mb-4">
                        <div className="text-6xl font-black text-gradient-premium mb-3 group-hover:scale-110 transition-transform duration-500">60%</div>
                        <div className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-500">
                          <div className="w-4 h-4 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full animate-luxury-pulse"></div>
                        </div>
                      </div>
                      <div className="font-medium text-slate-600 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100 transition-colors duration-500 mb-4">
                        Superior Talent Acquisition
                      </div>
                      <div className="w-full bg-gradient-to-r from-emerald-100 to-teal-100 dark:from-emerald-950 dark:to-teal-950 rounded-full h-1 opacity-0 group-hover:opacity-100 transition-all duration-700">
                        <div className="h-1 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-full transition-all duration-1000 group-hover:w-[60%] w-0"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </HoverCardTrigger>
              <HoverCardContent className="w-96 glass-card border-slate-200/30 dark:border-slate-700/30">
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold flex items-center gap-2">
                    <div className="p-2 bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900 dark:to-teal-900 rounded-lg">
                      <BsPeopleFill className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    Talent Acquisition Excellence Metrics
                  </h4>
                  <div className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Quality Score Improvement</span>
                      <span className="font-semibold text-emerald-600">60%</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Time-to-Hire Reduction</span>
                      <span className="font-semibold text-teal-600">75%</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Cultural Fit Accuracy</span>
                      <span className="font-semibold text-emerald-600">99.2%</span>
                    </div>
                  </div>
                  <div className="p-3 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/30 rounded-xl border border-emerald-100 dark:border-emerald-800/30">
                    <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                      60% improvement in talent acquisition quality through our proprietary agentic recruitment models 
                      that eliminate bias and identify top performers with unprecedented accuracy.
                    </p>
                  </div>
                </div>
              </HoverCardContent>
            </HoverCard>

            <HoverCard>
              <HoverCardTrigger asChild>
                <div className="relative group cursor-pointer stat-card">
                  <div className="relative glass-card text-center p-8 rounded-3xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-700 border-slate-200/30 dark:border-slate-700/30 overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-purple-50/50 dark:from-purple-950/30 rounded-full blur-2xl -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-1000"></div>
                    
                    <div className="relative z-10">
                      <div className="relative mb-4">
                        <div className="text-6xl font-black text-gradient-premium mb-3 group-hover:scale-110 transition-transform duration-500">₹2.5Cr+</div>
                        <div className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-500">
                          <div className="w-4 h-4 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full animate-luxury-pulse"></div>
                        </div>
                      </div>
                      <div className="font-medium text-slate-600 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100 transition-colors duration-500 mb-4">
                        Enterprise Value Generated
                      </div>
                      <div className="w-full bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-950 dark:to-pink-950 rounded-full h-1 opacity-0 group-hover:opacity-100 transition-all duration-700">
                        <div className="h-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full transition-all duration-1000 group-hover:w-[85%] w-0"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </HoverCardTrigger>
              <HoverCardContent className="w-96 glass-card border-slate-200/30 dark:border-slate-700/30">
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold flex items-center gap-2">
                    <div className="p-2 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900 dark:to-pink-900 rounded-lg">
                      <HiArrowTrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    Enterprise Value Breakdown
                  </h4>
                  <div className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Cost Savings</span>
                      <span className="font-semibold text-emerald-600">₹1.8Cr</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Efficiency Gains</span>
                      <span className="font-semibold text-blue-600">₹50L</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-slate-50/50 dark:bg-slate-800/30 rounded-lg">
                      <span>Risk Mitigation</span>
                      <span className="font-semibold text-purple-600">₹20L</span>
                    </div>
                  </div>
                  <div className="p-3 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30 rounded-xl border border-purple-100 dark:border-purple-800/30">
                    <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                      Our clients have generated over ₹2.5 Crores in measurable enterprise value through 
                      reduced operational costs, improved hiring efficiency, and enhanced compliance automation.
                    </p>
                  </div>
                </div>
              </HoverCardContent>
            </HoverCard>
          </div>
        </section>
        
        {/* Ultra-Premium CTA Section */}
        <section className="w-full py-20 md:py-32 relative overflow-hidden">
          
            <div className="container text-center relative z-10">
                <div className="max-w-5xl mx-auto space-y-12">
                    {/* Premium badge */}
                    <div className="relative group inline-block">
                      <Badge variant="outline" className="relative px-8 py-3 glass-card border-slate-200/50 dark:border-slate-700/50">
                        <div className="flex items-center gap-3">
                          <div className="p-1.5 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-lg">
                            <HiArrowRight className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                          </div>
                          <span className="text-gradient-luxury font-semibold">Ready for Transformation</span>
                        </div>
                      </Badge>
                    </div>
                    
                    {/* Ultra-premium headline */}
                    <div className="space-y-6">
                      <h2 className="text-4xl font-black tracking-tight sm:text-6xl lg:text-7xl font-headline">
                        <span className="block text-gradient-luxury">Ready to Experience the</span>
                        <span className="block text-gradient-premium mt-2">Agentic HR Revolution?</span>
                      </h2>
                      
                      <div className="glass-card p-8 rounded-2xl max-w-4xl mx-auto">
                        <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed font-light">
                          BearSystemsHRT© orchestrates intelligent agents across recruitment, compliance, performance intelligence, and workforce optimization.
                        </p>
                        <p className="text-lg text-slate-500 dark:text-slate-400 mt-4 leading-relaxed">
                          Join the vanguard of organizations pioneering our exclusive launch program.
                        </p>
                      </div>
                    </div>
                    
                    {/* Premium value proposition card */}
                    <div className="relative group max-w-4xl mx-auto">
                      <div className="absolute -inset-2 bg-gradient-to-br from-emerald-100/30 via-teal-100/20 to-emerald-100/30 dark:from-emerald-900/20 dark:via-teal-900/15 dark:to-emerald-900/20 rounded-3xl blur-lg group-hover:blur-xl transition-all duration-1000"></div>
                      
                      <div className="relative glass-card p-8 rounded-3xl border-slate-200/30 dark:border-slate-700/30">
                        <div className="space-y-6">
                          <div className="flex items-center justify-center gap-4 mb-6">
                            <div className="p-3 bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900 dark:to-teal-900 rounded-2xl">
                              <HiArrowTrendingUp className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
                            </div>
                            <div className="w-16 h-px bg-gradient-to-r from-emerald-200 to-teal-200 dark:from-emerald-700 dark:to-teal-700"></div>
                            <div className="p-3 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-2xl">
                              <TbBrain className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                            </div>
                          </div>
                          
                          <p className="text-slate-600 dark:text-slate-300 leading-relaxed font-medium">
                            Unite with industry visionaries already experiencing <span className="font-bold text-gradient-premium">90% operational transformation</span> and <span className="font-bold text-gradient-premium">10x enhanced talent outcomes</span> through our proprietary agentic recruitment and legal intelligence models.
                          </p>
                          
                          <div className="flex flex-col sm:flex-row gap-6 items-center justify-center pt-4">
                            <div className="text-center space-y-2">
                              <div className="flex items-center gap-2 justify-center">
                                <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-lg">
                                  <span className="text-2xl">📧</span>
                                </div>
                                <div>
                                  <p className="font-bold text-lg text-gradient-premium">admin@bearsystems.co.in</p>
                                  <p className="text-sm text-slate-500 dark:text-slate-400">Agentic Intelligence Response within 24 hours</p>
                                </div>
                              </div>
                            </div>
                            
                            <div className="relative group/cta">
                              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 rounded-2xl blur opacity-25 group-hover/cta:opacity-75 transition-all duration-700 animate-premium-glow"></div>
                              <Button asChild size="lg" className="relative px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 rounded-2xl shadow-2xl hover:shadow-blue-500/25 transition-all duration-500 font-semibold text-lg">
                                <a href="mailto:admin@bearsystems.co.in?subject=Revolutionary HR Transformation - BearSystemsHRT Demo Request">
                                  <div className="flex items-center gap-3">
                                    <RiStarSFill className="h-5 w-5 group-hover/cta:rotate-12 transition-transform duration-500" />
                                    <span>Get Started Today</span>
                                    <HiArrowRight className="h-5 w-5 group-hover/cta:translate-x-2 transition-transform duration-500" />
                                  </div>
                                </a>
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                </div>
            </div>
        </section>

        {/* Ultra-Premium Features Section - Unified Background */}
        <section id="features" ref={gsapFeaturesRef} className="w-full py-8 sm:py-12 md:py-16 lg:py-24 xl:py-32 relative overflow-hidden section-mobile sm:ipad-section lg:ipad-landscape-section">
          
          <div className="container px-4 md:px-6 relative z-10">
            <div className="flex flex-col items-center justify-center space-y-8 text-center">
              {/* Premium section badge */}
              <div className="relative group">
                <Badge variant="outline" className="relative px-6 py-3 glass-card border-slate-200/50 dark:border-slate-700/50">
                  <span className="text-gradient-luxury font-medium">AI Technology Platform</span>
                </Badge>
              </div>
              
              <div className="space-y-6 max-w-5xl">
                <h2 className="text-4xl font-black tracking-tight sm:text-6xl lg:text-7xl font-headline">
                  <span className="block text-gradient-luxury">Advanced AI Agents</span>
                  <span className="block text-gradient-premium mt-2">For Indian HR Excellence</span>
                </h2>
                <div className="glass-card p-6 rounded-2xl max-w-4xl mx-auto">
                  <p className="text-xl text-slate-600 dark:text-slate-300 md:text-2xl leading-relaxed font-light">
                    Advanced AI platform with specialized <span className="font-semibold text-gradient-premium">Recruitment Intelligence</span> and comprehensive <span className="font-semibold text-gradient-premium">Legal Compliance Engine</span>.
                  </p>
                  <p className="text-lg text-slate-500 dark:text-slate-400 mt-4 leading-relaxed">
                    Powered by extensive <span className="font-medium text-blue-600 dark:text-blue-400">Indian hiring intelligence</span>, delivering exceptional accuracy and complete <span className="font-medium text-emerald-600 dark:text-emerald-400">regulatory compliance</span>.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Ultra-Premium Agent Cards - Enhanced Mobile & iPad */}
            <div className="mx-auto grid max-w-7xl items-start gap-6 sm:gap-8 grid-cols-1 lg:grid-cols-2 mt-12 sm:mt-16 lg:mt-20 px-4 sm:px-6 lg:px-0 cards-mobile sm:ipad-grid lg:ipad-landscape-grid">
              {agentFeatures.map((feature, index) => (
                <div key={feature.title} className="relative group feature-card">
                  {/* Sophisticated glow effect */}
                  <div className="absolute -inset-2 bg-gradient-to-br from-blue-100/50 via-purple-100/30 to-blue-100/50 dark:from-blue-900/30 dark:via-purple-900/20 dark:to-blue-900/30 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-1000"></div>
                  
                  <div className="relative glass-card p-8 rounded-3xl hover:shadow-2xl transition-all duration-700 border-slate-200/30 dark:border-slate-700/30 overflow-hidden hover:scale-[1.02]">
                    {/* Premium background patterns */}
                    <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-blue-50/30 via-purple-50/20 to-transparent dark:from-blue-950/20 dark:via-purple-950/10 rounded-full blur-2xl -translate-y-20 translate-x-20 group-hover:scale-150 transition-transform duration-1000"></div>
                    <div className="absolute bottom-0 left-0 w-32 h-32 bg-gradient-to-tr from-purple-50/20 to-transparent dark:from-purple-950/10 rounded-full blur-xl translate-y-16 -translate-x-16 group-hover:scale-125 transition-transform duration-1000"></div>
                    
                    <div className="relative z-10">
                      <div className="flex items-start gap-6 mb-6">
                        <div className="relative group/icon">
                          <div className="relative p-4 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 rounded-2xl border border-slate-200 dark:border-slate-600">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg"></div>
                          </div>
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-3">
                            <h3 className="text-2xl font-bold font-headline text-gradient-luxury group-hover:text-gradient-premium transition-colors duration-500">
                              {feature.title}
                            </h3>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="relative">
                                  <div className="absolute -inset-1 bg-gradient-to-r from-emerald-200 to-teal-200 dark:from-emerald-800 dark:to-teal-800 rounded-full blur-sm"></div>
                                  <div className="relative flex items-center gap-2 text-xs font-semibold bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/50 dark:to-teal-950/50 px-3 py-2 rounded-full border border-emerald-200/50 dark:border-emerald-800/50">
                                      <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
                                      </span>
                                      <span className="text-emerald-700 dark:text-emerald-400">{feature.status}</span>
                                  </div>
                                </div>
                              </TooltipTrigger>
                              <TooltipContent side="top" className="glass-card">
                                <p>Agent is currently active and processing in real-time</p>
                              </TooltipContent>
                            </Tooltip>
                          </div>
                          <p className="text-slate-600 dark:text-slate-300 leading-relaxed group-hover:text-slate-800 dark:group-hover:text-slate-200 transition-colors duration-500">
                            {feature.description}
                          </p>
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="p-1.5 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900 dark:to-pink-900 rounded-lg">
                            <RiStarSFill className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                          </div>
                          <h4 className="font-semibold text-lg text-gradient-luxury">Core Capabilities</h4>
                        </div>
                        
                        <div className="grid gap-3">
                          {feature.capabilities.map((cap, idx) => (
                             <div key={cap} className="group/item relative">
                               <div className="absolute -inset-1 bg-gradient-to-r from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-700 rounded-xl opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                               <div className="relative flex items-start gap-4 p-3 rounded-xl group-hover/item:bg-white/50 dark:group-hover/item:bg-slate-800/30 transition-all duration-300">
                                 <div className="relative mt-1">
                                   <div className="absolute -inset-1 bg-gradient-to-br from-emerald-200 to-teal-200 dark:from-emerald-800 dark:to-teal-800 rounded-full blur-sm opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                                   <span className="w-3 h-3 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full"></span>
                                 </div>
                                 <span className="text-slate-600 dark:text-slate-300 group-hover/item:text-slate-800 dark:group-hover/item:text-slate-200 transition-colors duration-300 leading-relaxed font-medium">
                                   {cap}
                                 </span>
                               </div>
                             </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
              
              {/* Ultra-Premium Consensus Section - Unified Background */}
              <div className="mt-24">
               <div className="relative group max-w-6xl mx-auto">
                 
                 <div className="relative glass-card p-12 rounded-3xl border-slate-200/30 dark:border-slate-700/30 overflow-hidden">
                   {/* Premium background patterns */}
                   <div className="absolute inset-0 opacity-[0.02] dark:opacity-[0.05]">
                     <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                       <defs>
                         <pattern id="luxury-dots" width="40" height="40" patternUnits="userSpaceOnUse">
                           <circle cx="20" cy="20" r="1" fill="currentColor"/>
                         </pattern>
                       </defs>
                       <rect width="100%" height="100%" fill="url(#luxury-dots)" />
                     </svg>
                   </div>
                   
                   <div className="relative z-10 text-center space-y-8">
                     {/* Premium agent icons */}
                     <div className="flex items-center justify-center gap-6 mb-8">
                       {[
                         { name: 'Technical Intelligence', color: 'from-blue-500 to-blue-600' },
                         { name: 'Cultural Intelligence', color: 'from-purple-500 to-purple-600' },
                         { name: 'Legal Compliance', color: 'from-emerald-500 to-emerald-600' },
                         { name: 'Experience Intelligence', color: 'from-orange-500 to-orange-600' }
                       ].map((agent, idx) => (
                         <div key={idx} className="relative group/agent">
                           <div className="absolute -inset-2 bg-gradient-to-br from-slate-200/50 to-slate-100/50 dark:from-slate-700/30 dark:to-slate-600/30 rounded-2xl blur-sm group-hover/agent:blur-md transition-all duration-500"></div>
                           <Tooltip>
                             <TooltipTrigger asChild>
                               <div className={`relative p-4 bg-gradient-to-br ${agent.color} rounded-2xl shadow-lg group-hover/agent:scale-110 group-hover/agent:rotate-3 transition-all duration-500 cursor-pointer`}>
                                 <div className="h-8 w-8 bg-white/20 rounded-lg border border-white/30"></div>
                               </div>
                             </TooltipTrigger>
                             <TooltipContent className="glass-card">
                               <p className="font-medium">{agent.name}</p>
                             </TooltipContent>
                           </Tooltip>
                         </div>
                       ))}
                     </div>
                     
                     <div className="space-y-6">
                       <h3 className="text-3xl font-bold font-headline text-gradient-luxury">
                         Consensus-Driven Agentic Intelligence
                       </h3>
                       <div className="glass-card p-6 rounded-2xl max-w-4xl mx-auto">
                         <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                           All four autonomous agents analyze simultaneously and orchestrate consensus-driven final assessments. 
                           <span className="font-semibold text-gradient-premium"> Zero single points of failure</span>, 
                           <span className="font-semibold text-gradient-premium"> zero human bias</span> — pure collective AI intelligence working in perfect harmony.
                         </p>
                       </div>
                       
                       {/* Premium metrics */}
                       <div className="flex items-center justify-center gap-12 pt-6">
                         <Tooltip>
                           <TooltipTrigger asChild>
                             <div className="text-center group/metric cursor-pointer">
                               <div className="relative">
                                 <div className="absolute -inset-2 bg-gradient-to-br from-blue-200/30 to-purple-200/30 dark:from-blue-800/20 dark:to-purple-800/20 rounded-2xl blur-sm group-hover/metric:blur-md transition-all duration-500"></div>
                                 <div className="relative text-3xl font-black text-gradient-premium group-hover/metric:scale-110 transition-transform duration-300">4</div>
                               </div>
                               <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-1">Autonomous Agents</div>
                             </div>
                           </TooltipTrigger>
                           <TooltipContent className="glass-card">
                             <p>Technical • Experience • Cultural • Legal Intelligence</p>
                           </TooltipContent>
                         </Tooltip>
                         
                         <div className="w-16 h-px bg-gradient-to-r from-transparent via-slate-300 dark:via-slate-600 to-transparent"></div>
                         
                         <Tooltip>
                           <TooltipTrigger asChild>
                             <div className="text-center group/metric cursor-pointer">
                               <div className="relative">
                                 <div className="absolute -inset-2 bg-gradient-to-br from-emerald-200/30 to-teal-200/30 dark:from-emerald-800/20 dark:to-teal-800/20 rounded-2xl blur-sm group-hover/metric:blur-md transition-all duration-500"></div>
                                 <div className="relative text-3xl font-black text-gradient-premium group-hover/metric:scale-110 transition-transform duration-300">99.2%</div>
                               </div>
                               <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-1">Bias-Free Accuracy</div>
                             </div>
                           </TooltipTrigger>
                           <TooltipContent className="glass-card">
                             <p>Verified bias-free decision making accuracy</p>
                           </TooltipContent>
                         </Tooltip>
                         
                         <div className="w-16 h-px bg-gradient-to-r from-transparent via-slate-300 dark:via-slate-600 to-transparent"></div>
                         
                         <Tooltip>
                           <TooltipTrigger asChild>
                             <div className="text-center group/metric cursor-pointer">
                               <div className="relative">
                                 <div className="absolute -inset-2 bg-gradient-to-br from-red-200/30 to-orange-200/30 dark:from-red-800/20 dark:to-orange-800/20 rounded-2xl blur-sm group-hover/metric:blur-md transition-all duration-500"></div>
                                 <div className="relative text-3xl font-black text-gradient-premium group-hover/metric:scale-110 transition-transform duration-300">0</div>
                               </div>
                               <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-1">Human Bias</div>
                             </div>
                           </TooltipTrigger>
                           <TooltipContent className="glass-card">
                             <p>Complete elimination of human bias in all decisions</p>
                           </TooltipContent>
                         </Tooltip>
                       </div>
                     </div>
                   </div>
                 </div>
               </div>
             </div>
          </div>
        </section>

        {/* Ultra-Premium Learning & Development Section */}
        <section id="learning" className="w-full py-6 sm:py-8 md:py-12 lg:py-16 xl:py-24 relative overflow-hidden section-mobile sm:ipad-section lg:ipad-landscape-section">
          
          <div className="container px-4 md:px-6 relative z-10">
            <div className="flex flex-col items-center justify-center space-y-8 text-center">
              <div className="relative group inline-block">
                <Badge variant="outline" className="relative px-8 py-3 glass-card border-slate-200/50 dark:border-slate-700/50">
                  <span className="text-gradient-luxury font-semibold">Learning & Development Solutions</span>
                </Badge>
              </div>
              
              <div className="space-y-6">
                <h2 className="text-4xl font-black tracking-tight sm:text-6xl font-headline">
                  <span className="block text-gradient-luxury">Comprehensive Learning Pathways</span>
                  <span className="block text-gradient-premium mt-2">with Agentic Intelligence</span>
                </h2>
                
                <div className="glass-card p-8 rounded-2xl max-w-5xl mx-auto">
                  <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed font-light">
                    Transform candidate development through AI-powered learning pathways that provide agentic comparison with industry peers and cutting-edge career guidance based on real-time market trends and data analytics.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mx-auto grid max-w-7xl items-start gap-8 sm:grid-cols-1 lg:grid-cols-3 mt-20">
              {learningFeatures.map((feature, index) => (
                <div key={feature.title} className="relative group">
                  {/* Ultra-premium glow effect */}
                  <div className="absolute -inset-2 bg-gradient-to-br from-emerald-100/20 via-teal-100/15 to-emerald-100/20 dark:from-emerald-900/15 dark:via-teal-900/10 dark:to-emerald-900/15 rounded-3xl blur-lg group-hover:blur-xl transition-all duration-1000 opacity-0 group-hover:opacity-100"></div>
                  
                  <Card className="relative glass-card border-slate-200/30 dark:border-slate-700/30 hover:border-slate-300/50 dark:hover:border-slate-600/50 transition-all duration-500 group overflow-hidden">
                    {/* Subtle background pattern */}
                    <div className="absolute inset-0 opacity-[0.02] dark:opacity-[0.05]">
                      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                          <pattern id={`learning-dots-${index}`} width="25" height="25" patternUnits="userSpaceOnUse">
                            <circle cx="12.5" cy="12.5" r="0.8" fill="currentColor"/>
                          </pattern>
                        </defs>
                        <rect width="100%" height="100%" fill={`url(#learning-dots-${index})`} />
                      </svg>
                    </div>
                    
                    <CardHeader className="relative">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="relative group/icon">
                          <div className="relative p-3 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 rounded-xl border border-slate-200 dark:border-slate-600">
                            <div className="w-6 h-6 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-lg"></div>
                          </div>
                        </div>
                        <div className="flex-1">
                          <CardTitle className="font-headline text-lg group-hover:text-gradient-luxury transition-all duration-500">{feature.title}</CardTitle>
                        </div>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300 leading-relaxed group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-colors duration-500">{feature.description}</p>
                    </CardHeader>
                    <CardContent className="relative">
                      <div className="space-y-4">
                        <h4 className="text-sm font-semibold flex items-center gap-2">
                          <div className="p-1 bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900 dark:to-teal-900 rounded-md">
                            <RiStarSFill className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                          </div>
                          Core Intelligence Features
                        </h4>
                        
                        <div className="space-y-3">
                          {feature.features.map((feat, idx) => (
                            <div key={feat} className="group/item relative">
                              <div className="absolute -inset-1 bg-gradient-to-r from-slate-100/50 to-slate-50/50 dark:from-slate-800/30 dark:to-slate-700/30 rounded-lg opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                              <div className="relative flex items-start gap-3 p-2 rounded-lg group-hover/item:bg-white/30 dark:group-hover/item:bg-slate-800/20 transition-all duration-300">
                                <div className="relative mt-1">
                                  <div className="absolute -inset-0.5 bg-gradient-to-br from-emerald-200 to-teal-200 dark:from-emerald-800 dark:to-teal-800 rounded-full blur-sm opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                                  <span className="w-3 h-3 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full"></span>
                                </div>
                                <span className="text-sm text-slate-600 dark:text-slate-300 group-hover/item:text-slate-800 dark:group-hover/item:text-slate-200 transition-colors duration-300 leading-relaxed">{feat}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>

            {/* Ultra-Premium Learning Intelligence Summary */}
            <div className="relative group mt-20 max-w-5xl mx-auto">
              <div className="absolute -inset-4 bg-gradient-to-br from-emerald-100/20 via-teal-100/15 to-emerald-100/20 dark:from-emerald-900/15 dark:via-teal-900/10 dark:to-emerald-900/15 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-1000"></div>
              
              <Card className="relative glass-card border-slate-200/30 dark:border-slate-700/30 overflow-hidden">
                <div className="absolute inset-0 opacity-[0.01] dark:opacity-[0.02]">
                  <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <pattern id="learning-summary-pattern" width="35" height="35" patternUnits="userSpaceOnUse">
                        <circle cx="17.5" cy="17.5" r="1" fill="currentColor"/>
                      </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#learning-summary-pattern)" />
                  </svg>
                </div>
                
                <CardContent className="pt-12 pb-8 relative text-center">
                  <div className="relative group/target mb-8">
                    <div className="absolute -inset-3 bg-gradient-to-br from-emerald-200/50 to-teal-200/50 dark:from-emerald-800/30 dark:to-teal-800/30 rounded-2xl blur-lg group-hover/target:blur-xl transition-all duration-500"></div>
                    <div className="relative w-20 h-20 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-950/50 dark:to-teal-950/50 rounded-2xl flex items-center justify-center mx-auto border border-emerald-200/30 dark:border-emerald-700/30 group-hover:scale-110 transition-transform duration-500">
                      <TbTarget className="h-10 w-10 text-gradient-luxury" />
                    </div>
                  </div>
                  
                  <h3 className="text-2xl font-bold mb-6 font-headline text-gradient-luxury">Personalized Career Intelligence</h3>
                  
                  <div className="max-w-3xl mx-auto space-y-4">
                    <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-lg font-light">
                      Our agentic learning system creates individualized development pathways by analyzing peer performance data, 
                      market demand signals, and emerging skill trends to ensure every candidate stays ahead of the curve with 
                      data-driven career guidance tailored to their unique professional journey.
                    </p>
                    
                    <div className="flex items-center justify-center gap-8 pt-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gradient-premium">500K+</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Career Pathways</div>
                      </div>
                      <div className="w-px h-12 bg-slate-200 dark:bg-slate-700"></div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gradient-luxury">99.7%</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Accuracy Rate</div>
                      </div>
                      <div className="w-px h-12 bg-slate-200 dark:bg-slate-700"></div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gradient-premium">24/7</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">AI Learning</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Ultra-Premium Legal Compliance Section */}
        <section id="compliance" className="w-full py-6 sm:py-8 md:py-12 lg:py-16 xl:py-24 relative overflow-hidden section-mobile sm:ipad-section lg:ipad-landscape-section">
          
          <div className="container px-4 md:px-6 relative z-10">
            <div className="flex flex-col items-center justify-center space-y-8 text-center">
              <div className="relative group inline-block">
                <Badge variant="outline" className="relative px-8 py-3 glass-card border-slate-200/50 dark:border-slate-700/50">
                  <span className="text-gradient-luxury font-semibold">Legal Compliance Solutions</span>
                </Badge>
              </div>
              
              <div className="space-y-6">
                <h2 className="text-4xl font-black tracking-tight sm:text-6xl font-headline">
                  <span className="block text-gradient-luxury">Autonomous Legal</span>
                  <span className="block text-gradient-premium mt-2">Compliance Mastery</span>
                </h2>
                
                <div className="glass-card p-8 rounded-2xl max-w-5xl mx-auto">
                  <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed font-light">
                    Bear Systems processes ensure complete legal compliance through our proprietary AI that continuously monitors 
                    and updates from the latest legal documents across the internet, powered by our in-house trained legal intelligence models.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mx-auto grid max-w-7xl items-start gap-8 sm:grid-cols-1 lg:grid-cols-3 mt-20">
              {complianceFeatures.map((feature, index) => (
                <div key={feature.title} className="relative group">
                  {/* Ultra-premium glow effect */}
                  <div className="absolute -inset-2 bg-gradient-to-br from-blue-100/20 via-indigo-100/15 to-blue-100/20 dark:from-blue-900/15 dark:via-indigo-900/10 dark:to-blue-900/15 rounded-3xl blur-lg group-hover:blur-xl transition-all duration-1000 opacity-0 group-hover:opacity-100"></div>
                  
                  <Card className="relative glass-card border-slate-200/30 dark:border-slate-700/30 hover:border-slate-300/50 dark:hover:border-slate-600/50 transition-all duration-500 group overflow-hidden">
                    {/* Subtle background pattern */}
                    <div className="absolute inset-0 opacity-[0.02] dark:opacity-[0.05]">
                      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                          <pattern id={`compliance-dots-${index}`} width="25" height="25" patternUnits="userSpaceOnUse">
                            <circle cx="12.5" cy="12.5" r="0.8" fill="currentColor"/>
                          </pattern>
                        </defs>
                        <rect width="100%" height="100%" fill={`url(#compliance-dots-${index})`} />
                      </svg>
                    </div>
                    
                    <CardHeader className="relative">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="relative group/icon">
                          <div className="relative p-3 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 rounded-xl border border-slate-200 dark:border-slate-600">
                            <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg"></div>
                          </div>
                        </div>
                        <div className="flex-1">
                          <CardTitle className="font-headline text-lg group-hover:text-gradient-luxury transition-all duration-500">{feature.title}</CardTitle>
                        </div>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300 leading-relaxed group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-colors duration-500">{feature.description}</p>
                    </CardHeader>
                    <CardContent className="relative">
                      <div className="space-y-4">
                        <h4 className="text-sm font-semibold flex items-center gap-2">
                          <div className="p-1 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900 dark:to-indigo-900 rounded-md">
                            <RiStarSFill className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                          </div>
                          Legal Intelligence Features
                        </h4>
                        
                        <div className="space-y-3">
                          {feature.features.map((feat, idx) => (
                            <div key={feat} className="group/item relative">
                              <div className="absolute -inset-1 bg-gradient-to-r from-slate-100/50 to-slate-50/50 dark:from-slate-800/30 dark:to-slate-700/30 rounded-lg opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                              <div className="relative flex items-start gap-3 p-2 rounded-lg group-hover/item:bg-white/30 dark:group-hover/item:bg-slate-800/20 transition-all duration-300">
                                <div className="relative mt-1">
                                  <div className="absolute -inset-0.5 bg-gradient-to-br from-blue-200 to-indigo-200 dark:from-blue-800 dark:to-indigo-800 rounded-full blur-sm opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                                  <span className="w-3 h-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full"></span>
                                </div>
                                <span className="text-sm text-slate-600 dark:text-slate-300 group-hover/item:text-slate-800 dark:group-hover/item:text-slate-200 transition-colors duration-300 leading-relaxed">{feat}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>

            {/* Ultra-Premium Legal Intelligence Summary */}
            <div className="relative group mt-20 max-w-6xl mx-auto">
              <div className="absolute -inset-4 bg-gradient-to-br from-blue-100/20 via-indigo-100/15 to-blue-100/20 dark:from-blue-900/15 dark:via-indigo-900/10 dark:to-blue-900/15 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-1000"></div>
              
              <Card className="relative glass-card border-slate-200/30 dark:border-slate-700/30 overflow-hidden">
                <div className="absolute inset-0 opacity-[0.01] dark:opacity-[0.02]">
                  <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <pattern id="compliance-summary-pattern" width="35" height="35" patternUnits="userSpaceOnUse">
                        <circle cx="17.5" cy="17.5" r="1" fill="currentColor"/>
                      </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#compliance-summary-pattern)" />
                  </svg>
                </div>
                
                <CardContent className="pt-12 pb-8 relative">
                  <div className="flex items-center justify-center gap-8 mb-8">
                    <div className="relative group/brain">
                      <div className="absolute -inset-3 bg-gradient-to-br from-blue-200/50 to-indigo-200/50 dark:from-blue-800/30 dark:to-indigo-800/30 rounded-2xl blur-lg group-hover/brain:blur-xl transition-all duration-500"></div>
                      <div className="relative w-20 h-20 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/50 dark:to-indigo-950/50 rounded-2xl flex items-center justify-center border border-blue-200/30 dark:border-blue-700/30 group-hover:scale-110 transition-transform duration-500">
                        <TbBrain className="h-10 w-10 text-gradient-luxury" />
                      </div>
                    </div>
                    
                    <div className="w-20 h-px bg-gradient-to-r from-slate-300 via-slate-200 to-slate-300 dark:from-slate-600 dark:via-slate-700 dark:to-slate-600"></div>
                    
                    <div className="relative group/check">
                      <div className="absolute -inset-3 bg-gradient-to-br from-emerald-200/50 to-teal-200/50 dark:from-emerald-800/30 dark:to-teal-800/30 rounded-2xl blur-lg group-hover/check:blur-xl transition-all duration-500"></div>
                      <div className="relative w-20 h-20 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-950/50 dark:to-teal-950/50 rounded-2xl flex items-center justify-center border border-emerald-200/30 dark:border-emerald-700/30 group-hover:scale-110 transition-transform duration-500">
                        <HiOutlineClipboardDocumentCheck className="h-10 w-10 text-gradient-premium" />
                      </div>
                    </div>
                  </div>
                  
                  <h3 className="text-2xl font-bold mb-8 font-headline text-center text-gradient-luxury">Real-Time Legal Intelligence Updates</h3>
                  
                  <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    <div className="relative group/item">
                      <div className="absolute -inset-2 bg-gradient-to-br from-blue-100/30 to-indigo-100/20 dark:from-blue-900/20 dark:to-indigo-900/15 rounded-2xl blur-sm group-hover/item:blur-md transition-all duration-500 opacity-0 group-hover/item:opacity-100"></div>
                      <div className="relative glass-card p-6 rounded-2xl space-y-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900 dark:to-indigo-900 rounded-lg">
                            <HiBolt className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                          </div>
                          <h4 className="font-bold text-slate-700 dark:text-slate-300">Autonomous Document Monitoring</h4>
                        </div>
                        <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                          Our AI systems continuously scan government databases, legal repositories, and regulatory websites 
                          to capture the latest updates in Indian labor laws and compliance requirements.
                        </p>
                        
                        <div className="flex items-center gap-4 pt-2">
                          <div className="text-center">
                            <div className="text-lg font-bold text-gradient-premium">10M+</div>
                            <div className="text-xs text-slate-500 dark:text-slate-400">Documents Scanned</div>
                          </div>
                          <div className="w-px h-8 bg-slate-200 dark:bg-slate-700"></div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-gradient-luxury">24/7</div>
                            <div className="text-xs text-slate-500 dark:text-slate-400">Monitoring</div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="relative group/item">
                      <div className="absolute -inset-2 bg-gradient-to-br from-emerald-100/30 to-teal-100/20 dark:from-emerald-900/20 dark:to-teal-900/15 rounded-2xl blur-sm group-hover/item:blur-md transition-all duration-500 opacity-0 group-hover/item:opacity-100"></div>
                      <div className="relative glass-card p-6 rounded-2xl space-y-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900 dark:to-teal-900 rounded-lg">
                            <TbBrain className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                          </div>
                          <h4 className="font-bold text-slate-700 dark:text-slate-300">In-House Legal AI Training</h4>
                        </div>
                        <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                          Proprietary machine learning models trained specifically on Indian legal frameworks ensure 
                          accurate interpretation and implementation of complex regulatory requirements.
                        </p>
                        
                        <div className="flex items-center gap-4 pt-2">
                          <div className="text-center">
                            <div className="text-lg font-bold text-gradient-luxury">99.8%</div>
                            <div className="text-xs text-slate-500 dark:text-slate-400">Legal Accuracy</div>
                          </div>
                          <div className="w-px h-8 bg-slate-200 dark:bg-slate-700"></div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-gradient-premium">Real-time</div>
                            <div className="text-xs text-slate-500 dark:text-slate-400">Updates</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section id="about" className="w-full py-12 md:py-24 lg:py-32 relative overflow-hidden">
          
             <div className="container px-4 md:px-6 relative z-10">
                <div className="flex flex-col items-center justify-center space-y-8 text-center">
                    <div className="space-y-6">
                        <div className="relative group inline-block">
                          <Badge variant="outline" className="relative px-8 py-3 glass-card border-slate-200/50 dark:border-slate-700/50">
                            <span className="text-gradient-luxury font-semibold">Enterprise Technology Platform</span>
                          </Badge>
                        </div>
                        
                        <h2 className="text-4xl font-black tracking-tight sm:text-6xl lg:text-7xl font-headline">
                          <span className="block text-gradient-luxury">End-to-End HR Intelligence</span>
                          <span className="block text-gradient-premium mt-2">Orchestration Platform</span>
                        </h2>
                        
                        <div className="glass-card p-8 rounded-2xl max-w-5xl mx-auto">
                          <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed font-light">
                             From recruitment intelligence to compliance mastery, performance tracking to payroll optimization - BearSystemsHRT© orchestrates every aspect of HR operations through our proprietary agentic models engineered specifically for Indian organizations.
                          </p>
                          <p className="text-lg text-slate-500 dark:text-slate-400 mt-4 leading-relaxed">
                            Experience the future of human resources through autonomous intelligence agents.
                          </p>
                        </div>
                    </div>
                </div>
                <div className="mx-auto grid max-w-6xl items-start gap-8 sm:grid-cols-1 lg:grid-cols-2 mt-16">
                    {techFeatures.map((feature, index) => (
                        <div key={feature.title} className="relative group">
                          {/* Ultra-premium glow effect */}
                          <div className="absolute -inset-2 bg-gradient-to-br from-blue-100/30 via-purple-100/20 to-blue-100/30 dark:from-blue-900/20 dark:via-purple-900/15 dark:to-blue-900/20 rounded-3xl blur-lg group-hover:blur-xl transition-all duration-1000 opacity-0 group-hover:opacity-100"></div>
                          
                          <Card className="relative glass-card border-slate-200/30 dark:border-slate-700/30 hover:border-slate-300/50 dark:hover:border-slate-600/50 transition-all duration-500 group overflow-hidden">
                            {/* Subtle background pattern */}
                            <div className="absolute inset-0 opacity-[0.02] dark:opacity-[0.05]">
                              <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                                <defs>
                                  <pattern id={`premium-dots-${index}`} width="30" height="30" patternUnits="userSpaceOnUse">
                                    <circle cx="15" cy="15" r="1" fill="currentColor"/>
                                  </pattern>
                                </defs>
                                <rect width="100%" height="100%" fill={`url(#premium-dots-${index})`} />
                              </svg>
                            </div>
                            
                            <CardHeader className="relative">
                                {/* Premium value indicator */}
                                <div className="flex items-center gap-3 mb-4">
                                  <div className="relative">
                                    <div className="absolute -inset-1 bg-gradient-to-r from-emerald-200 to-teal-200 dark:from-emerald-800 dark:to-teal-800 rounded-lg blur-sm"></div>
                                    <div className="relative bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/50 dark:to-teal-950/50 px-4 py-2 rounded-lg border border-emerald-200/50 dark:border-emerald-800/50">
                                      <span className="text-gradient-luxury font-bold text-sm">{feature.value}</span>
                                    </div>
                                  </div>
                                </div>
                                
                                <CardTitle className="font-headline text-xl leading-tight group-hover:text-gradient-luxury transition-all duration-500">
                                  {feature.title}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="relative space-y-6">
                                <p className="text-slate-600 dark:text-slate-300 leading-relaxed group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-colors duration-500">{feature.description}</p>
                                
                                <div className="space-y-4">
                                  <h4 className="text-sm font-semibold flex items-center gap-2">
                                    <div className="p-1 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-md">
                                      <RiStarSFill className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    Premium Capabilities
                                  </h4>
                                  
                                  <div className="space-y-3">
                                    {feature.points.map((point, idx) => (
                                      <div key={point} className="group/item relative">
                                        <div className="absolute -inset-1 bg-gradient-to-r from-slate-100/50 to-slate-50/50 dark:from-slate-800/30 dark:to-slate-700/30 rounded-lg opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                                        <div className="relative flex items-start gap-3 p-2 rounded-lg group-hover/item:bg-white/30 dark:group-hover/item:bg-slate-800/20 transition-all duration-300">
                                          <div className="relative mt-1">
                                            <div className="absolute -inset-0.5 bg-gradient-to-br from-emerald-200 to-teal-200 dark:from-emerald-800 dark:to-teal-800 rounded-full blur-sm opacity-0 group-hover/item:opacity-100 transition-all duration-300"></div>
                                            <div className="relative w-2 h-2 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full group-hover/item:scale-125 transition-transform duration-300"></div>
                                          </div>
                                          <span className="text-sm text-slate-600 dark:text-slate-300 group-hover/item:text-slate-800 dark:group-hover/item:text-slate-200 transition-colors duration-300 leading-relaxed">{point}</span>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                            </CardContent>
                          </Card>
                        </div>
                    ))}
                </div>
            </div>
        </section>

         <section className="w-full py-12 md:py-24 lg:py-32 relative overflow-hidden">
            
            <div className="container px-4 md:px-6 relative z-10">
                <div className="flex flex-col items-center justify-center space-y-8 text-center">
                    <div className="relative group inline-block">
                      <Badge variant="outline" className="relative px-8 py-3 glass-card border-slate-200/50 dark:border-slate-700/50">
                        <span className="text-gradient-luxury font-semibold">Platform Advantages</span>
                      </Badge>
                    </div>
                    
                    <h2 className="text-4xl font-black tracking-tight sm:text-6xl font-headline">
                        <span className="block text-gradient-luxury">Why BearSystemsHRT© Pioneers</span>
                        <span className="block text-gradient-premium mt-2">the Future of Human Resources</span>
                    </h2>
                    
                    <div className="glass-card p-8 rounded-2xl max-w-5xl mx-auto">
                      <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed font-light">
                        While others deliver fragmented solutions, BearSystemsHRT© orchestrates complete HR transformation through proprietary agentic intelligence models designed specifically for Indian organizations and regulatory excellence.
                      </p>
                    </div>
                </div>
                
                {/* Ultra-Premium Feature Cards */}
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-16">
                    {[
                      { icon: HiMiniCpuChip, title: "Complete Agentic HR Intelligence", desc: "End-to-end agentic solution from recruitment intelligence to performance management and compliance mastery" },
                      { icon: TbBrain, title: "Proprietary Agentic Models", desc: "Recruitment and Legal intelligence engines engineered from inception for the Indian market" },
                      { icon: HiArrowTrendingUp, title: "Pioneering Agentic Innovation", desc: "First-to-market with comprehensive agentic HR intelligence constellation platform" },
                      { title: "Enterprise-Ready Intelligence", desc: "Military-grade security with seamless agentic integration capabilities" }
                    ].map((feature, index) => (
                      <div key={feature.title} className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-br from-blue-100/20 via-purple-100/15 to-blue-100/20 dark:from-blue-900/15 dark:via-purple-900/10 dark:to-blue-900/15 rounded-2xl blur-sm group-hover:blur-md transition-all duration-500 opacity-0 group-hover:opacity-100"></div>
                        
                        <Card className="relative text-center glass-card border-slate-200/30 dark:border-slate-700/30 hover:border-slate-300/50 dark:hover:border-slate-600/50 transition-all duration-500 group overflow-hidden">
                          <div className="absolute inset-0 opacity-[0.02] dark:opacity-[0.03]">
                            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                              <defs>
                                <pattern id={`dots-${index}`} width="25" height="25" patternUnits="userSpaceOnUse">
                                  <circle cx="12.5" cy="12.5" r="0.8" fill="currentColor"/>
                                </pattern>
                              </defs>
                              <rect width="100%" height="100%" fill={`url(#dots-${index})`} />
                            </svg>
                          </div>
                          
                          <CardContent className="pt-8 pb-6 relative">
                              <div className="mb-6">
                                  <div className="relative group/icon">
                                    <div className="absolute -inset-2 bg-gradient-to-br from-blue-200/50 to-purple-200/50 dark:from-blue-800/30 dark:to-purple-800/30 rounded-xl blur-sm group-hover/icon:blur-md transition-all duration-500"></div>
                                    <div className="relative w-16 h-16 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50 rounded-xl flex items-center justify-center mx-auto border border-slate-200/30 dark:border-slate-700/30 group-hover:scale-110 transition-transform duration-500">
                                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg"></div>
                                    </div>
                                  </div>
                              </div>
                              <h3 className="font-bold text-lg font-headline mb-3 group-hover:text-gradient-luxury transition-all duration-500">{feature.title}</h3>
                              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-colors duration-500">{feature.desc}</p>
                          </CardContent>
                        </Card>
                      </div>
                    ))}
                </div>
                
                 {/* Ultra-Premium Comparison Table */}
                 <div className="relative group mt-20 max-w-7xl mx-auto">
                   <div className="absolute -inset-4 bg-gradient-to-br from-blue-100/20 via-purple-100/15 to-blue-100/20 dark:from-blue-900/15 dark:via-purple-900/10 dark:to-blue-900/15 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-1000"></div>
                   
                   <Card className="relative glass-card border-slate-200/30 dark:border-slate-700/30 overflow-hidden">
                      <div className="absolute inset-0 opacity-[0.01] dark:opacity-[0.02]">
                        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                          <defs>
                            <pattern id="table-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
                              <circle cx="20" cy="20" r="1" fill="currentColor"/>
                            </pattern>
                          </defs>
                          <rect width="100%" height="100%" fill="url(#table-pattern)" />
                        </svg>
                      </div>
                      
                      <CardHeader className="relative text-center space-y-4 pb-8">
                          <CardTitle className="text-2xl font-headline">Competitive Intelligence Analysis</CardTitle>
                          <p className="text-slate-600 dark:text-slate-300 leading-relaxed max-w-3xl mx-auto">See how BearSystemsHRT© compares to traditional and basic AI solutions across critical HR intelligence dimensions</p>
                      </CardHeader>
                      <CardContent className="relative pb-8">
                          <div className="glass-card p-3 sm:p-6 rounded-xl">
                            {/* Mobile-responsive table wrapper with enhanced mobile support */}
                            <div className="overflow-x-auto -mx-3 sm:mx-0">
                              <div className="min-w-[800px] sm:min-w-full">
                                <Table className="table-mobile">
                                  <TableHeader>
                                      <TableRow className="border-slate-200/50 dark:border-slate-700/50 hover:bg-slate-50/50 dark:hover:bg-slate-800/20">
                                          <TableHead className="min-w-[160px] sm:w-[200px] md:w-[280px] font-bold text-slate-700 dark:text-slate-300 text-xs sm:text-sm px-2 sm:px-4">Intelligence Feature</TableHead>
                                          <TableHead className="text-center font-semibold text-slate-600 dark:text-slate-400 text-xs sm:text-sm min-w-[120px] px-1 sm:px-4">Traditional HR</TableHead>
                                          <TableHead className="text-center font-semibold text-slate-600 dark:text-slate-400 text-xs sm:text-sm min-w-[120px] px-1 sm:px-4">Basic AI</TableHead>
                                          <TableHead className="text-center font-bold bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50 text-gradient-luxury border-l-2 border-blue-200/50 dark:border-blue-800/50 text-xs sm:text-sm min-w-[160px] px-1 sm:px-4">BearSystemsHRT©</TableHead>
                                      </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                      {competitiveData.map((row, index) => (
                                          <TableRow key={row.feature} className="border-slate-200/30 dark:border-slate-700/30 hover:bg-slate-50/30 dark:hover:bg-slate-800/10 transition-colors duration-300 group/row">
                                              <TableCell className="font-semibold text-slate-700 dark:text-slate-300 group-hover/row:text-slate-900 dark:group-hover/row:text-slate-100 transition-colors duration-300 text-xs sm:text-sm px-2 sm:px-4" data-label="Feature">{row.feature}</TableCell>
                                              <TableCell className="text-center text-slate-500 dark:text-slate-400 font-medium text-xs sm:text-sm px-1 sm:px-4" data-label="Traditional">{row.traditional}</TableCell>
                                              <TableCell className="text-center text-slate-500 dark:text-slate-400 font-medium text-xs sm:text-sm px-1 sm:px-4" data-label="Basic AI">{row.basic}</TableCell>
                                              <TableCell className="text-center font-bold bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-blue-950/30 dark:to-purple-950/30 text-gradient-luxury border-l-2 border-blue-200/30 dark:border-blue-800/30 group-hover/row:bg-gradient-to-r group-hover/row:from-blue-100/50 group-hover/row:to-purple-100/50 dark:group-hover/row:from-blue-900/30 dark:group-hover/row:to-purple-900/30 transition-all duration-300 text-xs sm:text-sm px-1 sm:px-4" data-label="BearSystemsHRT©">{row.our}</TableCell>
                                          </TableRow>
                                      ))}
                                  </TableBody>
                                </Table>
                              </div>
                            </div>
                          </div>
                      </CardContent>
                   </Card>
                 </div>
            </div>
        </section>

        <section id="contact" className="w-full py-12 md:py-24 relative overflow-hidden">
            
            <div className="container text-center relative z-10">
                <div className="max-w-5xl mx-auto space-y-10">
                    <div className="relative group inline-block">
                      <Badge variant="outline" className="relative px-8 py-3 glass-card border-slate-200/50 dark:border-slate-700/50">
                        <span className="text-gradient-luxury font-semibold">Enterprise Contact</span>
                      </Badge>
                    </div>
                    
                    <h2 className="text-4xl font-black tracking-tight sm:text-6xl lg:text-7xl font-headline">
                      <span className="block text-gradient-luxury">Ready for Enterprise</span>
                      <span className="block text-gradient-premium mt-2">AI Transformation?</span>
                    </h2>
                    
                    <div className="glass-card p-8 rounded-2xl max-w-4xl mx-auto">
                      <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed font-light">
                        Join the exclusive launch program for BearSystemsHRT© - advanced AI platform engineered specifically for Indian enterprises and compliance excellence.
                      </p>
                      <p className="text-lg text-slate-500 dark:text-slate-400 mt-4 leading-relaxed">
                        Experience <span className="font-medium text-emerald-600">streamlined hiring</span>, <span className="font-medium text-blue-600">intelligent matching</span>, and <span className="font-medium text-purple-600">complete compliance</span> for Indian organizations.
                      </p>
                    </div>
                    
                    {/* Ultra-Premium CTA Button */}
                    <div className="relative group inline-block pt-6">
                      <div className="absolute -inset-2 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 rounded-3xl blur-lg opacity-30 group-hover:opacity-75 transition-all duration-1000 group-hover:duration-200 animate-premium-glow"></div>
                      <Button asChild size="lg" className="relative px-12 py-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 rounded-3xl shadow-2xl hover:shadow-blue-500/25 transition-all duration-500 group font-bold text-xl">
                        <a href="mailto:admin@bearsystems.co.in?subject=Transform HR Operations - BearSystemsHRT Demo Request&body=Hello Bear Systems Team,%0D%0A%0D%0AI am interested in learning how BearSystemsHRT© can transform our HR operations. Please provide more information about:%0D%0A%0D%0A- Platform capabilities%0D%0A- Implementation process%0D%0A- Pricing and packages%0D%0A- Demo access%0D%0A%0D%0ACompany: %0D%0AName: %0D%0ARole: %0D%0APhone: %0D%0AEmail: %0D%0A%0D%0AThank you!">
                          <div className="flex items-center gap-4">
                            <TbBrain className="h-6 w-6 group-hover:rotate-12 transition-transform duration-500" />
                            <span>Get Started Today</span>
                            <HiArrowRight className="h-6 w-6 group-hover:translate-x-2 transition-transform duration-500" />
                          </div>
                        </a>
                      </Button>
                    </div>
                </div>
            </div>
        </section>

      </main>
      <footer className="border-t relative overflow-hidden">
        
        <div className="container py-16 relative z-10">
            <div className="grid md:grid-cols-4 gap-12">
                <div className="space-y-6">
                     <Link href="/" className="flex items-center space-x-3 group">
                        <div className="relative">
                          <div className="relative">
                            <AppLogo />
                          </div>
                        </div>
                        <span className="font-bold font-headline text-xl">Bear Systems <span className="text-gradient-luxury">HRT</span></span>
                      </Link>
                      <div className="glass-card p-6 rounded-xl space-y-4">
                        <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">Complete agentic HR intelligence platform powered by proprietary AI models. BearSystemsHRT© orchestrates recruitment, compliance, performance management, and more - engineered specifically for Indian organizations through advanced agentic intelligence.</p>
                        
                        <div className="space-y-3">
                          <div className="flex items-center gap-3">
                            <div className="p-1.5 bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900 dark:to-teal-900 rounded-lg">
                              <HiOutlineEnvelope className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                            </div>
                            <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">admin@bearsystems.co.in</span>
                          </div>
                          
                          <div className="flex items-center gap-3">
                            <div className="p-1.5 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-lg">
                              <HiMapPin className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            </div>
                            <span className="text-sm text-slate-600 dark:text-slate-400">India</span>
                          </div>
                        </div>
                        
                        <div className="relative group">
                          <Button variant="outline" asChild className="relative w-full glass-card border-slate-200/50 dark:border-slate-700/50 hover:border-slate-300/70 dark:hover:border-slate-600/70 transition-all duration-500">
                              <a href="https://bearsystems.co.in" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                                <HiArrowTopRightOnSquare className="h-4 w-4" />
                                Visit BearSystems.co.in
                              </a>
                          </Button>
                        </div>
                      </div>
                </div>
                
                <div className="md:col-start-3 space-y-6">
                    <h4 className="font-bold text-lg text-gradient-luxury">Quick Links</h4>
                    <div className="glass-card p-6 rounded-xl">
                      <ul className="space-y-4">
                          <li>
                            <Link href="/candidates" className="flex items-center gap-3 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors duration-300 group">
                              <div className="p-1 bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/50 dark:to-blue-950/50 rounded-md group-hover:scale-110 transition-transform duration-300">
                                <HiChatBubbleOvalLeft className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                              </div>
                              For Candidates
                            </Link>
                          </li>
                          <li>
                            <Link href="#contact" className="flex items-center gap-3 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors duration-300 group">
                              <div className="p-1 bg-gradient-to-br from-emerald-100 to-emerald-50 dark:from-emerald-900/50 dark:to-emerald-950/50 rounded-md group-hover:scale-110 transition-transform duration-300">
                                <HiRocketLaunch className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                              </div>
                              Get Started
                            </Link>
                          </li>
                          <li>
                            <a href="mailto:admin@bearsystems.co.in?subject=Demo Request - BearSystemsHRT Platform&body=Hello Bear Systems Team,%0D%0A%0D%0AI would like to request a demo of the BearSystemsHRT© agentic AI platform. Please provide information about:%0D%0A%0D%0A- Platform demonstration%0D%0A- Key features and capabilities%0D%0A- Implementation timeline%0D%0A- Pricing options%0D%0A%0D%0ACompany: %0D%0AName: %0D%0ARole: %0D%0APhone: %0D%0AEmail: %0D%0A%0D%0AThank you!" className="flex items-center gap-3 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors duration-300 group">
                              <div className="p-1 bg-gradient-to-br from-purple-100 to-purple-50 dark:from-purple-900/50 dark:to-purple-950/50 rounded-md group-hover:scale-110 transition-transform duration-300">
                                <HiPlay className="h-3 w-3 text-purple-600 dark:text-purple-400" />
                              </div>
                              Request Demo
                            </a>
                          </li>
                          <li>
                            <a href="mailto:admin@bearsystems.co.in?subject=Partnership Inquiry - BearSystemsHRT Collaboration&body=Hello Bear Systems Team,%0D%0A%0D%0AI am interested in exploring partnership opportunities with BearSystemsHRT©. Please provide information about:%0D%0A%0D%0A- Partnership models available%0D%0A- Integration possibilities%0D%0A- Revenue sharing structures%0D%0A- Technical requirements%0D%0A%0D%0ACompany: %0D%0AName: %0D%0ARole: %0D%0APhone: %0D%0AEmail: %0D%0A%0D%0AThank you!" className="flex items-center gap-3 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors duration-300 group">
                              <div className="p-1 bg-gradient-to-br from-orange-100 to-orange-50 dark:from-orange-900/50 dark:to-orange-950/50 rounded-md group-hover:scale-110 transition-transform duration-300">
                                <HiHandRaised className="h-3 w-3 text-orange-600 dark:text-orange-400" />
                              </div>
                              Partnership
                            </a>
                          </li>
                      </ul>
                    </div>
                </div>
                
                <div className="space-y-6">
                     <h4 className="font-bold text-lg text-gradient-premium">Experience Agentic Intelligence</h4>
                     <div className="glass-card p-6 rounded-xl space-y-6">
                       <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">Ready to revolutionize your HR operations through autonomous agentic intelligence?</p>
                       
                       <div className="relative group">
                         <Button asChild className="relative w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 shadow-lg hover:shadow-blue-500/25 transition-all duration-500 group font-semibold">
                            <a href="mailto:admin@bearsystems.co.in?subject=Experience the Future - BearSystemsHRT Demo Request&body=Hello Bear Systems Team,%0D%0A%0D%0AI am interested in experiencing the revolutionary BearSystemsHRT© agentic AI platform. Please provide more information about implementation and demo access.%0D%0A%0D%0ACompany: %0D%0AName: %0D%0ARole: %0D%0APhone: %0D%0A%0D%0AThank you!" className="flex items-center gap-2">
                              <TbBrain className="h-4 w-4 group-hover:rotate-12 transition-transform duration-500" />
                              Experience the Future
                            </a>
                         </Button>
                       </div>
                       
                       <div className="flex items-center gap-3 justify-center">
                         <div className="relative flex h-2 w-2">
                           <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                           <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
                         </div>
                         <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Agentic Intelligence Response within 24 hours</p>
                       </div>
                     </div>
                </div>
            </div>
            
            {/* Ultra-Premium Footer Bottom */}
            <div className="mt-16 pt-8 border-t border-slate-200/50 dark:border-slate-700/50">
              <div className="glass-card p-6 rounded-xl">
                <div className="flex flex-col md:flex-row justify-between items-center gap-6 text-sm">
                    <div className="flex items-center gap-4">
                      <p className="text-slate-600 dark:text-slate-400">© {currentYear} Bear Systems HRT. A proud product of BearSystems.co.in.</p>
                      <div className="hidden md:block w-px h-4 bg-slate-300 dark:bg-slate-600"></div>
                      <div className="flex items-center gap-2">
                        <div className="p-1 bg-gradient-to-br from-emerald-100 to-emerald-50 dark:from-emerald-900/50 dark:to-emerald-950/50 rounded-md">
                          <span className="w-2 h-2 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full"></span>
                        </div>
                        <span className="text-xs text-slate-500 dark:text-slate-400">Enterprise Security</span>
                      </div>
                    </div>
                    <div className="flex gap-6">
                        <Link href="/terms" className="text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors duration-300 flex items-center gap-2">
                          <HiDocumentText className="h-3 w-3" />
                          Terms of Service
                        </Link>
                        <Link href="/privacy" className="text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors duration-300 flex items-center gap-2">
                          <HiLockClosed className="h-3 w-3" />
                          Privacy
                        </Link>
                    </div>
                </div>
              </div>
            </div>
        </div>
      </footer>
    </div>
    </TooltipProvider>
  );
}
