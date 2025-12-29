
'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { CheckCircle, Zap, TrendingUp, Users, Shield, Gavel, Cpu, Scaling } from 'lucide-react';
import { Icons } from '@/components/icons';
import { RoiCalculator } from '@/components/roi-calculator';
import { ThemeToggle } from '@/components/ui/theme-toggle';

export default function LandingPage() {
  return (
    <div className="bg-background text-foreground overflow-x-hidden font-body">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
          <Link href="/" className="flex items-center gap-2">
            <Icons.logo className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold">BearSystems HR toolset</span>
          </Link>
          <nav className="hidden items-center gap-6 md:flex">
            <Link href="#features" className="text-sm font-medium hover:underline">
              Features
            </Link>
            <Link href="#roi-calculator" className="text-sm font-medium hover:underline">
              Calculator
            </Link>
            <Link href="#about" className="text-sm font-medium hover:underline">
              About Us
            </Link>
            <ThemeToggle />
            <Link href="/login">
              <Button>Sign In</Button>
            </Link>
          </nav>
          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle />
            <Link href="/login">
              <Button>Sign In</Button>
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative py-20 text-center container mx-auto px-4 md:px-6 overflow-hidden">
           <div className="absolute inset-0 -z-10 h-full w-full bg-background bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]"><div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-primary/20 opacity-20 blur-[100px]"></div></div>
          <div className="relative z-10 animate-fade-in-up font-headline">
             <h1 className="text-4xl md:text-6xl font-extrabold tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-primary via-primary/80 to-primary/90">
              AI-Powered HR Revolution
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-lg md:text-xl text-muted-foreground font-body">
              Turn ₹5,00,000 HR Costs into ₹50,000 AI Magic
            </p>
            <p className="mx-auto mt-2 max-w-3xl text-md md:text-lg font-body">
              Indian HR consultancies are saving 90% on screening costs while finding better candidates in 1/10th the time.
            </p>
            <div className="mt-8 flex justify-center gap-4">
                <Link href="/register">
                  <Button size="lg" className="bg-gradient-to-r from-primary to-primary/80 text-primary-foreground shadow-lg animate-in fade-in zoom-in-95 duration-500">Get Started Now</Button>
                </Link>
                <Link href="#roi-calculator">
                    <Button size="lg" variant="outline" className="shadow-lg animate-in fade-in zoom-in-95 duration-500 delay-100">Calculate My Savings</Button>
                </Link>
            </div>
            <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-3 animate-in fade-in-0 slide-in-from-bottom-12 duration-700 delay-200">
              <div className="flex flex-col items-center">
                <p className="text-4xl font-bold text-primary">95%</p>
                <p className="text-muted-foreground font-body">Faster Screening</p>
              </div>
              <div className="flex flex-col items-center">
                <p className="text-4xl font-bold text-primary">60%</p>
                <p className="text-muted-foreground font-body">Better Hire Quality</p>
              </div>
              <div className="flex flex-col items-center">
                <p className="text-4xl font-bold text-primary">₹2.5Cr+</p>
                <p className="text-muted-foreground font-body">Saved by Clients</p>
              </div>
            </div>
          </div>
        </section>

        {/* 4-Agent System Section */}
        <section id="features" className="py-20 bg-muted/50">
          <div className="container mx-auto px-4 md:px-6">
            <div className="text-center">
              <h2 className="text-3xl md:text-4xl font-bold font-headline">4-Agent Agentic AI System</h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
                While Others Use Simple Keywords, We Deploy 4 AI Specialists.
              </p>
            </div>
            <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: Cpu, title: 'Technical Agent', description: 'Analyzes programming languages, frameworks, certifications with real-time skill trend analysis.' },
                { icon: TrendingUp, title: 'Experience Evaluator', description: 'Validates work history, analyzes career progression, identifies leadership indicators.' },
                { icon: Users, title: 'Cultural Fit Analyzer', description: 'Detects communication style, soft skills, personality insights, team collaboration potential.' },
                { icon: Gavel, title: 'Legal Compliance Guardian', description: 'Bias detection, Indian labor law compliance, fairness assessment, audit trails.' }
              ].map((feature, i) => (
                  <Card key={feature.title} className="hover:shadow-xl hover:-translate-y-1 transition-all duration-300 animate-in fade-in slide-in-from-bottom-8" style={{ animationDelay: `${i * 150}ms`}}>
                      <CardHeader>
                          <feature.icon className="h-8 w-8 mb-2 text-primary"/>
                          <CardTitle className="font-headline">{feature.title}</CardTitle>
                      </CardHeader>
                      <CardContent>
                          <CardDescription>{feature.description}</CardDescription>
                      </CardContent>
                  </Card>
              ))}
            </div>
             <div className="text-center mt-12 animate-in fade-in-0 duration-500 delay-500">
                <p className="text-lg font-semibold">📄 Resume Input ➡️ 4 AI Agents ➡️ ✅ Consensus Score</p>
                <p className="mx-auto mt-2 max-w-2xl text-muted-foreground">
                    All four agents analyze simultaneously and build consensus on the final assessment. No single point of failure, no human bias - just pure AI intelligence working together.
                </p>
            </div>
          </div>
        </section>

        {/* Technical Architecture Section */}
        <section id="about" className="py-20">
          <div className="container mx-auto px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold font-headline">Beyond Simple AI</h2>
              <p className="mx-auto mt-4 max-w-3xl text-lg text-muted-foreground">
                While competitors claim "AI-powered", we've built the most sophisticated hiring intelligence system designed for the complexities of Indian talent acquisition.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-12 items-center">
               <div className="space-y-8">
                  <div className="flex gap-4">
                     <CheckCircle className="h-8 w-8 text-green-500 mt-1 shrink-0"/>
                     <div>
                        <h3 className="text-xl font-bold font-headline">Fine-Tuned Bias Mitigation Model (99.2% Bias-Free)</h3>
                        <p className="text-muted-foreground mt-1">Our proprietary model trained on 500K+ Indian hiring scenarios identifies and eliminates unconscious bias.</p>
                     </div>
                  </div>
                  <div className="flex gap-4">
                     <Zap className="h-8 w-8 text-yellow-500 mt-1 shrink-0"/>
                     <div>
                        <h3 className="text-xl font-bold font-headline">Advanced Resume Intelligence (10x More Insights)</h3>
                        <p className="text-muted-foreground mt-1">Reads between the lines - detects career gaps, hidden strengths, growth potential with Indian context understanding.</p>
                     </div>
                  </div>
                  <div className="flex gap-4">
                     <Gavel className="h-8 w-8 text-blue-500 mt-1 shrink-0"/>
                     <div>
                        <h3 className="text-xl font-bold font-headline">Legal Compliance Engine (100% Compliant)</h3>
                        <p className="text-muted-foreground mt-1">Built-in Indian Labor Law database with 2024 updates, automated compliance checking for every hiring decision.</p>
                     </div>
                  </div>
                   <div className="flex gap-4">
                     <Shield className="h-8 w-8 text-indigo-500 mt-1 shrink-0"/>
                     <div>
                        <h3 className="text-xl font-bold font-headline">Enterprise-Grade Security (Military-Grade)</h3>
                        <p className="text-muted-foreground mt-1">AES-256 encryption, compressed storage architecture, and zero data leak guarantee with military-grade protection.</p>
                     </div>
                  </div>
               </div>
               <div className="grid grid-cols-2 gap-6 text-center">
                    <Card className="bg-muted/50 hover:shadow-md transition-shadow">
                        <CardContent className="p-6">
                            <p className="text-4xl font-bold text-primary font-headline">97.5%</p>
                            <p className="text-sm text-muted-foreground">AI Accuracy Rate</p>
                        </CardContent>
                    </Card>
                     <Card className="bg-muted/50 hover:shadow-md transition-shadow">
                        <CardContent className="p-6">
                            <p className="text-4xl font-bold text-primary font-headline">&lt;0.8s</p>
                            <p className="text-sm text-muted-foreground">Analysis Time</p>
                        </CardContent>
                    </Card>
                     <Card className="bg-muted/50 hover:shadow-md transition-shadow">
                        <CardContent className="p-6">
                            <p className="text-4xl font-bold text-primary font-headline">0</p>
                            <p className="text-sm text-muted-foreground">Bias Incidents</p>
                        </CardContent>
                    </Card>
                     <Card className="bg-muted/50 hover:shadow-md transition-shadow">
                        <CardContent className="p-6">
                            <p className="text-4xl font-bold text-primary font-headline">100%</p>
                            <p className="text-sm text-muted-foreground">Legal Compliance</p>
                        </CardContent>
                    </Card>
               </div>
            </div>
          </div>
        </section>

        {/* ROI Calculator Section */}
        <section id="roi-calculator" className="py-20 bg-muted/50">
            <div className="container mx-auto px-4 md:px-6 text-center">
                <h2 className="text-3xl md:text-4xl font-bold font-headline">See Your Exact Savings</h2>
                <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
                    Input your company details and discover how much you can save with AI-powered hiring.
                </p>
                <RoiCalculator />
            </div>
        </section>

        {/* CTA Section */}
        <section className="py-20">
          <div className="container mx-auto px-4 md:px-6 text-center">
            <h2 className="text-3xl md:text-4xl font-bold font-headline">Ready to Experience the Future?</h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
              While others are catching up to yesterday's technology, you can be using tomorrow's AI today.
            </p>
            <div className="mt-8">
                <Link href="/register">
                  <Button size="lg">Start Your Trial</Button>
                </Link>
            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 md:px-6 py-12">
            <div className="grid gap-8 md:grid-cols-3">
                <div>
                    <h3 className="font-bold text-lg font-headline">BearSystems HR toolset</h3>
                    <p className="mt-2 text-sm text-primary-foreground/80">
                        Revolutionizing HR operations with AI-powered resume screening and hiring intelligence. Built specifically for the Indian market with local expertise and compliance.
                    </p>
                </div>
                <div>
                    <h3 className="font-bold text-lg font-headline">Quick Links</h3>
                    <ul className="mt-2 space-y-1 text-sm">
                        <li><Link href="/login" className="hover:underline text-primary-foreground/80">Login</Link></li>
                        <li><Link href="/register" className="hover:underline text-primary-foreground/80">Sign Up</Link></li>
                        <li><Link href="#features" className="hover:underline text-primary-foreground/80">Features</Link></li>
                    </ul>
                </div>
                <div>
                    <h3 className="font-bold text-lg font-headline">Contact</h3>
                     <a href="mailto:admin@hrintel.pro" className="text-sm mt-1 hover:underline text-yellow-300">
                        info@bearsystems.co.in
                    </a>
                </div>
            </div>
          <div className="mt-8 border-t border-primary-foreground/20 pt-8 flex flex-col md:flex-row justify-between items-center text-sm">
            <p className="text-primary-foreground/60">&copy; 2025 BearSystems HR toolset. All rights reserved. | Made with ❤️ for Indian HR professionals</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
