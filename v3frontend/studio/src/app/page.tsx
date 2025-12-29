
'use client';

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { CheckCircle, ShieldCheck, Cpu, IndianRupee, Briefcase, Zap, BarChart, Users, BrainCircuit, Scale, ArrowRight, FileText as FileTextIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import CountUp from 'react-countup';
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Label } from "@/components/ui/label";
import { BearLogo } from "@/components/ui/bear-logo";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
// Temporarily commented out 3D components that might cause dependency issues
// import Silk from "@/Backgrounds/Silk/Silk";
// import ShinyText from "@/TextAnimations/ShinyText/ShinyText";
// import BlobCursor from "@/Animations/BlobCursor/BlobCursor";


const StatCard = ({ icon, value, label, color }: { icon: React.ElementType, value: string, label: string, color: string }) => {
    const Icon = icon;
    const ref = useRef(null);
    const isInView = useInView(ref, { once: true, margin: "-100px" });
    
    return (
        <motion.div
            ref={ref}
            initial={{ opacity: 0, y: 30, scale: 0.9 }}
            animate={isInView ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 30, scale: 0.9 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
        >
            <Card className="bg-card/80 backdrop-blur-sm border-border text-card-foreground hover:bg-card/90 shadow-lg hover:shadow-xl transition-all duration-300">
                <CardContent className="p-4 flex items-center gap-4">
                    <motion.div
                        initial={{ scale: 0, rotate: -180 }}
                        animate={isInView ? { scale: 1, rotate: 0 } : { scale: 0, rotate: -180 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                    >
                        <Icon className={`w-8 h-8 ${color}`} />
                    </motion.div>
                    <div>
                        <motion.div 
                            className="text-2xl font-bold text-foreground"
                            initial={{ opacity: 0 }}
                            animate={isInView ? { opacity: 1 } : { opacity: 0 }}
                            transition={{ duration: 0.5, delay: 0.4 }}
                        >
                            {value}
                        </motion.div>
                        <motion.p 
                            className="text-sm text-muted-foreground"
                            initial={{ opacity: 0 }}
                            animate={isInView ? { opacity: 1 } : { opacity: 0 }}
                            transition={{ duration: 0.5, delay: 0.5 }}
                        >
                            {label}
                        </motion.p>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
};

const FeatureCard = ({ icon, title, description, capabilities, status, statusColor }: { icon: React.ElementType, title: string, description: string, capabilities: string[], status: string, statusColor: string }) => {
    const Icon = icon;
    const ref = useRef(null);
    const isInView = useInView(ref, { once: true, margin: "-50px" });
    
    return (
        <motion.div
            ref={ref}
            initial={{ opacity: 0, y: 40 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
        >
            <Card className="bg-card flex flex-col h-full hover:shadow-xl hover:shadow-primary/5 transition-all duration-300 border-l-4 border-l-primary/20 hover:border-l-primary">
                <CardHeader>
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-4">
                            <motion.div 
                                className="p-3 bg-primary/10 rounded-lg"
                                whileHover={{ rotate: [0, -10, 10, 0], transition: { duration: 0.5 } }}
                            >
                                <Icon className="w-6 h-6 text-primary" />
                            </motion.div>
                            <div>
                                <CardTitle className="text-lg">{title}</CardTitle>
                            </div>
                        </div>
                        <Badge variant="outline" className={`border-${statusColor} text-${statusColor} bg-secondary`}>{status}</Badge>
                    </div>
                    <CardDescription className="pt-4">{description}</CardDescription>
                </CardHeader>
                <CardContent className="flex-grow">
                    <h4 className="font-semibold mb-2 text-sm">Core Capabilities:</h4>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                        {capabilities.map((cap, index) => (
                            <motion.li 
                                key={cap} 
                                className="flex items-start gap-2"
                                initial={{ opacity: 0, x: -20 }}
                                animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
                                transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
                            >
                                <CheckCircle className="w-4 h-4 mt-0.5 text-green-500 shrink-0" />
                                <span>{cap}</span>
                            </motion.li>
                        ))}
                    </ul>
                </CardContent>
            </Card>
        </motion.div>
    );
};

const TechPill = ({ icon, title, description }: { icon: React.ElementType, title: string, description: string }) => {
    const Icon = icon;
    return (
        <div className="flex items-start gap-4 p-4 rounded-lg bg-secondary">
            <Icon className="w-8 h-8 text-primary shrink-0 mt-1" />
            <div>
                <h3 className="font-semibold">{title}</h3>
                <p className="text-sm text-muted-foreground">{description}</p>
            </div>
        </div>
    );
}

export default function LandingPage() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [companySize, setCompanySize] = useState(100);
  const [monthlyHiring, setMonthlyHiring] = useState(10);
  const [avgSalary, setAvgSalary] = useState(5.0);
  const [costs, setCosts] = useState({ traditional: 0, withAI: 0, savings: 0 });

  useEffect(() => {
    setYear(new Date().getFullYear());
  }, []);

  useEffect(() => {
    const calculateCosts = () => {
        // Simplified calculation logic
        const traditionalCost = (companySize * 0.15 + monthlyHiring * 1.2) * avgSalary * 10000;
        const aiCost = traditionalCost * 0.65; // Assuming 35% savings
        const annualSavings = traditionalCost - aiCost;
        
        setCosts({
            traditional: traditionalCost,
            withAI: aiCost,
            savings: annualSavings
        });
    };
    calculateCosts();
  }, [companySize, monthlyHiring, avgSalary]);


  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
        {/* Premium Blob Cursor - Temporarily commented out */}
        {/* <BlobCursor 
            fillColor="#3b82f6"
            trailCount={3}
            sizes={[45, 90, 60]}
            opacities={[0.4, 0.3, 0.2]}
            fastDuration={0.1}
            slowDuration={0.6}
        /> */}
        
        {/* Header */}
        <motion.header 
            className="sticky top-0 z-50 px-4 lg:px-6 h-16 flex items-center bg-background/80 backdrop-blur-sm border-b"
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
        >
            <motion.div
                whileHover={{ scale: 1.05 }}
                transition={{ duration: 0.2 }}
            >
                <Link href="#" className="flex items-center justify-center">
                    <BearLogo size="md" />
                </Link>
            </motion.div>
            <nav className="ml-auto hidden md:flex gap-4 sm:gap-6 items-center">
                {[
                    { href: "#features", label: "Features" },
                    { href: "#calculator", label: "Calculator" },
                    { href: "#contact", label: "About Us" }
                ].map((item, index) => (
                    <motion.div
                        key={`header-nav-${index}-${item.label}`}
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: 0.1 + index * 0.1 }}
                    >
                        <Link href={item.href} className="text-sm font-medium hover:underline underline-offset-4 hover:text-primary transition-colors">
                            {item.label}
                        </Link>
                    </motion.div>
                ))}
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: 0.4 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <Button asChild variant="outline" className="hover:bg-primary hover:text-primary-foreground transition-all duration-300">
                        <Link href="/login">Sign In</Link>
                    </Button>
                </motion.div>
            </nav>
            <div className="md:hidden ml-auto">
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <Button asChild className="bg-primary hover:bg-primary/90 text-primary-foreground">
                        <Link href="/login">Sign In</Link>
                    </Button>
                </motion.div>
            </div>
        </motion.header>

        <main className="flex-1">
            {/* Hero Section */}
            <section className="w-full py-20 lg:py-32 xl:py-48 relative overflow-hidden">
                {/* Silk Background - Temporarily commented out */}
                {/* <div className="absolute inset-0 z-0">
                    <Silk 
                        speed={3}
                        scale={1.2}
                        color="#1e40af"
                        noiseIntensity={0.8}
                        rotation={0}
                    />
                </div> */}
                
                {/* Gradient overlay for better text readability */}
                <div className="absolute inset-0 z-10 bg-gradient-to-br from-background/98 via-background/90 to-background/95" />
                
                {/* Animated background elements */}
                <motion.div
                    className="absolute inset-0 z-20 opacity-20"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.2 }}
                    transition={{ duration: 2 }}
                >
                    <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-primary rounded-full animate-pulse" />
                    <div className="absolute top-3/4 right-1/3 w-1 h-1 bg-accent rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
                    <div className="absolute bottom-1/4 left-1/3 w-1.5 h-1.5 bg-primary rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
                </motion.div>
                
                <div className="container px-4 md:px-6 relative z-30">
                    <div className="grid gap-8 lg:grid-cols-2 lg:gap-12">
                        <div className="flex flex-col justify-center space-y-6">
                            <motion.div 
                                className="space-y-4"
                                initial={{ opacity: 0, x: -50 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                            >
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6, delay: 0.2 }}
                                    className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium"
                                >
                                    <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                                    Bear Systems HRT - Human Resources Tools
                                </motion.div>
                                
                                <motion.h1 
                                    className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none"
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.8, delay: 0.3 }}
                                >
                                    {/* ShinyText temporarily replaced with regular text */}
                                    <span className="bg-clip-text bg-gradient-to-r from-white via-blue-200 to-cyan-300 text-4xl sm:text-5xl xl:text-6xl font-bold tracking-tighter drop-shadow-lg">
                                        AI-Powered HR Revolution
                                    </span>
                                    {/* <ShinyText 
                                        text="AI-Powered HR Revolution"
                                        className="bg-clip-text bg-gradient-to-r from-white via-blue-200 to-cyan-300 text-4xl sm:text-5xl xl:text-6xl font-bold tracking-tighter drop-shadow-lg"
                                        speed={4}
                                    /> */}
                                </motion.h1>
                                
                                <motion.p 
                                    className="max-w-[600px] text-muted-foreground md:text-xl"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6, delay: 0.5 }}
                                >
                                    Transform <span className="font-bold text-destructive">₹5,00,000</span> HR costs into <span className="font-bold text-primary">₹50,000</span> AI-powered efficiency. Indian enterprises are achieving 90% cost reduction while improving candidate quality by 10x.
                                </motion.p>
                                
                                <motion.p 
                                    className="text-sm text-muted-foreground"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ duration: 0.6, delay: 0.7 }}
                                >
                                    Powered by 4 specialized AI agents with India's most advanced bias-free hiring intelligence.
                                </motion.p>
                            </motion.div>
                            
                            <motion.div 
                                className="flex flex-col gap-2 min-[400px]:flex-row"
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6, delay: 0.8 }}
                            >
                                <motion.div
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    <Button asChild size="lg" className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg hover:shadow-xl transition-all duration-300">
                                        <Link href="/signup">Get Started Now</Link>
                                    </Button>
                                </motion.div>
                                <motion.div
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    <Button asChild size="lg" variant="outline" className="border-primary text-primary hover:bg-primary hover:text-primary-foreground transition-all duration-300">
                                        <Link href="#calculator">Calculate Savings</Link>
                                    </Button>
                                </motion.div>
                            </motion.div>
                        </div>
                        
                        <motion.div 
                            className="flex flex-col justify-center space-y-4"
                            initial={{ opacity: 0, x: 50 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.8, delay: 0.4 }}
                        >
                            <StatCard icon={Zap} value="95%" label="Faster Screening" color="text-yellow-400" />
                            <StatCard icon={Users} value="60%" label="Better Hire Quality" color="text-green-400" />
                            <StatCard icon={IndianRupee} value="₹2.5Cr+" label="Saved by Clients" color="text-primary" />
                        </motion.div>
                    </div>
                </div>
            </section>
            
            {/* Onboarding Info */}
            <section id="contact" className="w-full py-12 md:py-20 lg:py-24 bg-gradient-to-br from-accent/5 to-primary/5">
                <motion.div 
                    className="container text-center"
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    viewport={{ once: true }}
                >
                    <motion.h2 
                        className="text-2xl font-bold tracking-tighter sm:text-3xl"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        viewport={{ once: true }}
                    >
                        Ready to Transform Your HR Operations?
                    </motion.h2>
                    <motion.p 
                        className="max-w-[700px] mx-auto text-muted-foreground md:text-lg mt-4"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.3 }}
                        viewport={{ once: true }}
                    >
                        We're onboarding select HR consultancies and enterprises. Contact us to get priority access to Bear Systems HRT and join the AI revolution.
                    </motion.p>
                    <motion.div 
                        className="mt-6"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.4 }}
                        viewport={{ once: true }}
                    >
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <Button variant="default" size="lg" asChild className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg hover:shadow-xl transition-all duration-300">
                               <a href="mailto:admin@bearsystems.co.in">
                                    📧 admin@bearsystems.co.in
                               </a>
                            </Button>
                        </motion.div>
                        <motion.p 
                            className="text-sm text-muted-foreground mt-2"
                            initial={{ opacity: 0 }}
                            whileInView={{ opacity: 1 }}
                            transition={{ duration: 0.6, delay: 0.6 }}
                            viewport={{ once: true }}
                        >
                            Response within 24 hours
                        </motion.p>
                    </motion.div>
                </motion.div>
            </section>

            {/* 4-Agent System */}
            <section id="features" className="w-full py-12 md:py-24 lg:py-32">
                 <div className="container px-4 md:px-6">
                    <motion.div 
                        className="flex flex-col items-center justify-center space-y-4 text-center"
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        viewport={{ once: true }}
                    >
                        <div className="space-y-2">
                            <motion.div 
                                className="inline-block rounded-lg bg-muted px-3 py-1 text-sm"
                                initial={{ opacity: 0, scale: 0.8 }}
                                whileInView={{ opacity: 1, scale: 1 }}
                                transition={{ duration: 0.5, delay: 0.2 }}
                                viewport={{ once: true }}
                            >
                                4-Agent Agentic AI System
                            </motion.div>
                            <motion.h2 
                                className="text-3xl font-bold tracking-tighter sm:text-5xl"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6, delay: 0.3 }}
                                viewport={{ once: true }}
                            >
                                While Others Use Simple Keywords, We Deploy 4 AI Specialists
                            </motion.h2>
                            <motion.p 
                                className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6, delay: 0.4 }}
                                viewport={{ once: true }}
                            >
                                Each agent brings domain expertise - like having a technical recruiter, experience analyst, culture expert, and legal consultant working simultaneously on every resume.
                            </motion.p>
                        </div>
                    </motion.div>
                    <motion.div 
                        className="mx-auto grid max-w-5xl grid-cols-1 items-stretch gap-6 py-12 md:grid-cols-2 lg:gap-8"
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        transition={{ duration: 0.8, delay: 0.5 }}
                        viewport={{ once: true }}
                    >
                         <FeatureCard 
                            icon={Cpu}
                            title="Technical Agent"
                            description="Analyzes programming languages, frameworks, certifications with real-time skill trend analysis"
                            capabilities={['Skill proficiency scoring', 'Certification validation', 'Technology trend mapping', 'Project complexity assessment']}
                            status="Active"
                            statusColor="green-500"
                        />
                         <FeatureCard 
                            icon={BarChart}
                            title="Experience Evaluator"
                            description="Validates work history, analyzes career progression, identifies leadership indicators"
                            capabilities={['Career trajectory analysis', 'Achievement quantification', 'Leadership potential detection', 'Industry experience mapping']}
                            status="Active"
                            statusColor="green-500"
                        />
                         <FeatureCard 
                            icon={Users}
                            title="Cultural Fit Analyzer"
                            description="Detects communication style, soft skills, personality insights, team collaboration potential"
                            capabilities={['Communication pattern analysis', 'Soft skill extraction', 'Team compatibility scoring', 'Cultural alignment assessment']}
                            status="Active"
                            statusColor="green-500"
                        />
                         <FeatureCard 
                            icon={ShieldCheck}
                            title="Legal Compliance Guardian"
                            description="Bias detection, Indian labor law compliance, fairness assessment, audit trails"
                            capabilities={['Unconscious bias detection', 'Legal compliance verification', 'Fairness scoring', 'Audit trail generation']}
                            status="Active"
                            statusColor="green-500"
                        />
                    </motion.div>
                     <motion.div 
                         className="text-center max-w-3xl mx-auto"
                         initial={{ opacity: 0, y: 30 }}
                         whileInView={{ opacity: 1, y: 0 }}
                         transition={{ duration: 0.8, delay: 0.3 }}
                         viewport={{ once: true }}
                     >
                        <div className="flex items-center justify-center gap-4 md:gap-8 text-muted-foreground mb-4">
                           <motion.div 
                               className="text-center"
                               initial={{ opacity: 0, scale: 0 }}
                               whileInView={{ opacity: 1, scale: 1 }}
                               transition={{ duration: 0.5, delay: 0.5 }}
                               viewport={{ once: true }}
                           >
                                <FileTextIcon className="w-10 h-10 mx-auto" />
                                <p className="text-sm mt-1">Resume Input</p>
                           </motion.div>
                           <motion.div
                               initial={{ opacity: 0, scale: 0 }}
                               whileInView={{ opacity: 1, scale: 1 }}
                               transition={{ duration: 0.3, delay: 0.7 }}
                               viewport={{ once: true }}
                           >
                               <ArrowRight className="w-8 h-8 shrink-0"/>
                           </motion.div>
                             <motion.div 
                                 className="text-center"
                                 initial={{ opacity: 0, scale: 0 }}
                                 whileInView={{ opacity: 1, scale: 1 }}
                                 transition={{ duration: 0.5, delay: 0.9 }}
                                 viewport={{ once: true }}
                             >
                                <div className="p-3 rounded-full bg-primary/10 inline-block">
                                   <div className="p-2 rounded-full bg-primary/20">
                                       <BrainCircuit className="w-10 h-10 text-primary" />
                                   </div>
                               </div>
                                <p className="text-sm mt-1">4 AI Agents</p>
                           </motion.div>
                           <motion.div
                               initial={{ opacity: 0, scale: 0 }}
                               whileInView={{ opacity: 1, scale: 1 }}
                               transition={{ duration: 0.3, delay: 1.1 }}
                               viewport={{ once: true }}
                           >
                               <ArrowRight className="w-8 h-8 shrink-0"/>
                           </motion.div>
                           <motion.div 
                               className="text-center"
                               initial={{ opacity: 0, scale: 0 }}
                               whileInView={{ opacity: 1, scale: 1 }}
                               transition={{ duration: 0.5, delay: 1.3 }}
                               viewport={{ once: true }}
                           >
                                <CheckCircle className="w-10 h-10 mx-auto text-green-500" />
                                <p className="text-sm mt-1">Consensus Score</p>
                           </motion.div>
                        </div>
                        <motion.h3 
                            className="text-xl font-bold"
                            initial={{ opacity: 0 }}
                            whileInView={{ opacity: 1 }}
                            transition={{ duration: 0.6, delay: 1.5 }}
                            viewport={{ once: true }}
                        >
                            Consensus-Driven Decision Making
                        </motion.h3>
                        <motion.p 
                            className="text-muted-foreground"
                            initial={{ opacity: 0 }}
                            whileInView={{ opacity: 1 }}
                            transition={{ duration: 0.6, delay: 1.7 }}
                            viewport={{ once: true }}
                        >
                            All four agents analyze simultaneously and build consensus on the final assessment. No single point of failure, no human bias - just pure AI intelligence working together.
                        </motion.p>
                     </motion.div>
                 </div>
            </section>

             {/* Advanced Architecture */}
            <section className="w-full py-12 md:py-24 lg:py-32 bg-muted">
                <div className="container px-4 md:px-6">
                    <div className="flex flex-col items-center justify-center space-y-4 text-center">
                        <div className="space-y-2">
                             <div className="inline-block rounded-lg bg-background px-3 py-1 text-sm">
                                Beyond Simple AI
                            </div>
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">
                                Advanced Technical Architecture That Actually Works
                            </h2>
                            <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                                While competitors claim "AI-powered", we've built the most sophisticated hiring intelligence system designed specifically for the complexities of Indian talent acquisition.
                            </p>
                        </div>
                    </div>
                     <div className="mx-auto grid max-w-5xl gap-8 py-12 lg:grid-cols-2">
                        <div className="space-y-4">
                            <h3 className="text-2xl font-bold">Fine-Tuned Bias Mitigation Model</h3>
                            <p className="text-green-500 font-semibold">99.2% Bias-Free</p>
                            <p className="text-muted-foreground">Our proprietary model trained on 500K+ Indian hiring scenarios identifies and eliminates unconscious bias.</p>
                            <ul className="space-y-2 text-sm">
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Real-time bias alerts prevent discriminatory decisions</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Ensures fair evaluation across gender, background, education institutions</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> India-specific bias patterns recognition</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Continuous learning from hiring outcomes</li>
                            </ul>
                        </div>
                        <div className="space-y-4">
                            <h3 className="text-2xl font-bold">Advanced Resume Intelligence</h3>
                            <p className="text-green-500 font-semibold">10x More Insights</p>
                            <p className="text-muted-foreground">Reads between the lines - detects career gaps, hidden strengths, growth potential with Indian context understanding.</p>
                             <ul className="space-y-2 text-sm">
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Understands Indian context: family breaks, diverse education systems</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Non-linear career path analysis and gap interpretation</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Hidden skill extraction from project descriptions</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Growth trajectory prediction with 94% accuracy</li>
                            </ul>
                        </div>
                        <div className="space-y-4">
                            <h3 className="text-2xl font-bold">Legal Compliance Engine</h3>
                             <p className="text-green-500 font-semibold">100% Compliant</p>
                            <p className="text-muted-foreground">Built-in Indian Labor Law database with 2024 updates, automated compliance checking for every hiring decision.</p>
                            <ul className="space-y-2 text-sm">
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Real-time legal compliance verification</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Automated audit trails for every decision</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Protection against discrimination lawsuits</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Integration with latest Indian labor law amendments</li>
                            </ul>
                        </div>
                        <div className="space-y-4">
                            <h3 className="text-2xl font-bold">Enterprise-Grade Security</h3>
                            <p className="text-green-500 font-semibold">Military-Grade</p>
                            <p className="text-muted-foreground">AES-256 encryption, compressed storage architecture, and zero data leak guarantee with military-grade protection.</p>
                            <ul className="space-y-2 text-sm">
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> AES-256 encryption for all sensitive data</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Compressed storage reduces costs by 80%</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> Zero-trust security architecture</li>
                                <li className="flex gap-2"><CheckCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" /> SOC 2 Type II compliance ready</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>
            
            {/* Competitive Analysis */}
            <section className="w-full py-12 md:py-24 lg:py-32">
                 <div className="container px-4 md:px-6">
                    <div className="flex flex-col items-center justify-center space-y-4 text-center">
                        <div className="space-y-2">
                             <div className="inline-block rounded-lg bg-muted px-3 py-1 text-sm">
                                Competitive Analysis
                            </div>
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">
                                Why We're Years Ahead Of The Competition
                            </h2>
                            <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                                Most HR tools are built for the global market. We're the only platform engineered specifically for Indian hiring challenges with cutting-edge AI architecture.
                            </p>
                        </div>
                    </div>

                    <div className="mx-auto grid max-w-5xl items-start gap-8 py-12 lg:grid-cols-2">
                        <div className="grid gap-6">
                            <TechPill icon={BrainCircuit} title="Multi-Agent Intelligence" description="While others use single AI models, we deploy 4 specialized agents working in parallel" />
                            <TechPill icon={Scale} title="Bias-Free Guarantee" description="Proprietary model trained on 500K+ scenarios ensures zero discrimination" />
                            <TechPill icon={IndianRupee} title="India-First Design" description="Built specifically for Indian hiring complexities and legal requirements" />
                            <TechPill icon={ShieldCheck} title="Enterprise Security" description="Military-grade encryption with compressed storage architecture" />
                        </div>
                        <div className="overflow-x-auto">
                           <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Feature</TableHead>
                                        <TableHead>Traditional ATS</TableHead>
                                        <TableHead>Basic AI Tools</TableHead>
                                        <TableHead className="bg-primary/10 text-primary">Our Agentic System</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {[
                                        { feature: 'Resume Analysis Method', traditional: 'Manual keyword matching', basic: 'Single AI model scanning', ours: '4-Agent collaborative analysis' },
                                        { feature: 'Bias Detection', traditional: 'Manual review (prone to bias)', basic: 'Basic sentiment analysis', ours: 'Proprietary bias mitigation model' },
                                        { feature: 'Legal Compliance', traditional: 'Manual compliance checking', basic: 'Generic global compliance', ours: 'Built-in Indian labor law engine' },
                                        { feature: 'Data Security', traditional: 'Basic password protection', basic: 'Standard encryption', ours: 'AES-256 + compressed storage' },
                                        { feature: 'Learning Capability', traditional: 'No learning', basic: 'Static configurations', ours: 'Continuous real-time learning' },
                                        { feature: 'Processing Speed', traditional: 'Hours per resume', basic: 'Minutes per resume', ours: 'Sub-second per resume' },
                                        { feature: 'Indian Context Understanding', traditional: 'None', basic: 'Limited', ours: 'Specialized for Indian market' },
                                    ].map(item => (
                                         <TableRow key={item.feature}>
                                            <TableCell className="font-medium">{item.feature}</TableCell>
                                            <TableCell>{item.traditional}</TableCell>
                                            <TableCell>{item.basic}</TableCell>
                                            <TableCell className="bg-primary/5 font-medium text-primary">{item.ours}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </div>
            </section>

             {/* ROI Calculator */}
            <section id="calculator" className="w-full py-12 md:py-24 lg:py-32 bg-muted">
                <div className="container grid items-center justify-center gap-8 px-4 text-center md:px-6">
                    <motion.div 
                        className="space-y-3"
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        viewport={{ once: true }}
                    >
                         <motion.div 
                             className="inline-block rounded-lg bg-background px-3 py-1 text-sm"
                             initial={{ opacity: 0, scale: 0.8 }}
                             whileInView={{ opacity: 1, scale: 1 }}
                             transition={{ duration: 0.5, delay: 0.2 }}
                             viewport={{ once: true }}
                         >
                            See the Numbers
                        </motion.div>
                        <motion.h2 
                            className="text-3xl font-bold tracking-tighter md:text-4xl/tight"
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.3 }}
                            viewport={{ once: true }}
                        >
                            See Your Exact Savings
                        </motion.h2>
                        <motion.p 
                            className="mx-auto max-w-[600px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed"
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.4 }}
                            viewport={{ once: true }}
                        >
                            Input your company details and discover how much you can save with AI-powered hiring.
                        </motion.p>
                    </motion.div>
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.5 }}
                        viewport={{ once: true }}
                    >
                        <Card className="w-full max-w-2xl mx-auto text-left shadow-2xl border-primary/20 hover:shadow-3xl transition-all duration-500">
                            <CardHeader className="bg-gradient-to-r from-primary/5 to-accent/5">
                                <CardTitle className="text-primary">Calculate Your Savings</CardTitle>
                                <CardDescription>See how much your company can save with Bear Systems HRT.</CardDescription>
                            </CardHeader>
                            <CardContent className="grid md:grid-cols-2 gap-8 p-6">
                                <div className="space-y-6">
                                    <motion.div
                                        initial={{ opacity: 0, x: -20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        transition={{ duration: 0.5, delay: 0.7 }}
                                        viewport={{ once: true }}
                                    >
                                        <Label className="text-sm font-medium">Company Size: {companySize} employees</Label>
                                        <Slider 
                                            value={[companySize]} 
                                            onValueChange={(val) => setCompanySize(val[0])} 
                                            min={10} 
                                            max={1000} 
                                            step={10} 
                                            className="mt-2"
                                        />
                                    </motion.div>
                                     <motion.div
                                         initial={{ opacity: 0, x: -20 }}
                                         whileInView={{ opacity: 1, x: 0 }}
                                         transition={{ duration: 0.5, delay: 0.8 }}
                                         viewport={{ once: true }}
                                     >
                                        <Label className="text-sm font-medium">Monthly Hiring: {monthlyHiring} positions</Label>
                                        <Slider 
                                            value={[monthlyHiring]} 
                                            onValueChange={(val) => setMonthlyHiring(val[0])} 
                                            min={1} 
                                            max={50} 
                                            step={1} 
                                            className="mt-2"
                                        />
                                     </motion.div>
                                     <motion.div
                                         initial={{ opacity: 0, x: -20 }}
                                         whileInView={{ opacity: 1, x: 0 }}
                                         transition={{ duration: 0.5, delay: 0.9 }}
                                         viewport={{ once: true }}
                                     >
                                        <Label className="text-sm font-medium">Avg HR Salary: ₹{avgSalary.toFixed(1)} L/year</Label>
                                        <Slider 
                                            value={[avgSalary]} 
                                            onValueChange={(val) => setAvgSalary(val[0])} 
                                            min={3} 
                                            max={10} 
                                            step={0.5} 
                                            className="mt-2"
                                        />
                                     </motion.div>
                                </div>
                                <motion.div 
                                    className="p-6 bg-gradient-to-br from-primary/5 to-accent/5 rounded-lg text-center flex flex-col justify-center border border-primary/20"
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    whileInView={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.6, delay: 1.0 }}
                                    viewport={{ once: true }}
                                >
                                    <p className="text-sm text-muted-foreground">Annual Savings</p>
                                    <motion.div 
                                        className="text-4xl font-bold text-primary my-2"
                                        initial={{ scale: 0 }}
                                        whileInView={{ scale: 1 }}
                                        transition={{ duration: 0.8, delay: 1.2, type: "spring", bounce: 0.4 }}
                                        viewport={{ once: true }}
                                    >
                                        ₹<CountUp end={costs.savings / 100000} decimals={1} duration={1.5} suffix=" L" />
                                    </motion.div>
                                    <div className="text-sm text-muted-foreground space-y-1">
                                        <p><span className="font-bold text-foreground">Traditional:</span> ₹<CountUp end={costs.traditional / 100000} decimals={1} duration={1.5} suffix=" L/year" /></p>
                                        <p><span className="font-bold text-foreground">With Bear Systems HRT:</span> ₹<CountUp end={costs.withAI / 100000} decimals={1} duration={1.5} suffix=" L/year" /></p>
                                    </div>
                                    <motion.p 
                                        className="text-xs text-primary mt-4 font-medium"
                                        initial={{ opacity: 0 }}
                                        whileInView={{ opacity: 1 }}
                                        transition={{ duration: 0.6, delay: 1.4 }}
                                        viewport={{ once: true }}
                                    >
                                        ~35% cost reduction • Break-even in ~7 months
                                    </motion.p>
                                </motion.div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>
            </section>
        </main>

        {/* Footer */}
        <footer className="border-t bg-background">
            <div className="container py-12 grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                 <div className="space-y-4">
                     <motion.div
                         initial={{ opacity: 0, y: 20 }}
                         whileInView={{ opacity: 1, y: 0 }}
                         transition={{ duration: 0.6 }}
                         viewport={{ once: true }}
                     >
                         <Link href="#" className="flex items-center justify-start">
                            <BearLogo size="sm" />
                        </Link>
                     </motion.div>
                    <motion.p 
                        className="text-sm text-muted-foreground"
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        viewport={{ once: true }}
                    >
                        Revolutionizing HR operations with AI-powered resume screening and hiring intelligence. Built specifically for the Indian market.
                    </motion.p>
                     <motion.p 
                         className="text-sm"
                         initial={{ opacity: 0 }}
                         whileInView={{ opacity: 1 }}
                         transition={{ duration: 0.6, delay: 0.3 }}
                         viewport={{ once: true }}
                     >
                         📧 <a href="mailto:admin@bearsystems.co.in" className="hover:underline hover:text-primary transition-colors">admin@bearsystems.co.in</a>
                     </motion.p>
                     <motion.p 
                         className="text-sm"
                         initial={{ opacity: 0 }}
                         whileInView={{ opacity: 1 }}
                         transition={{ duration: 0.6, delay: 0.4 }}
                         viewport={{ once: true }}
                     >
                         📍 India
                     </motion.p>
                     <motion.a 
                         href="https://bearsystems.co.in" 
                         target="_blank" 
                         rel="noopener noreferrer" 
                         className="text-sm font-semibold text-primary hover:underline flex items-center gap-1 hover:text-primary/80 transition-colors"
                         initial={{ opacity: 0 }}
                         whileInView={{ opacity: 1 }}
                         transition={{ duration: 0.6, delay: 0.5 }}
                         viewport={{ once: true }}
                         whileHover={{ x: 4 }}
                     >
                        Visit BearSystems.co.in <ArrowRight className="w-4 h-4" />
                     </motion.a>
                 </div>
                 <motion.div 
                     className="space-y-4"
                     initial={{ opacity: 0, y: 20 }}
                     whileInView={{ opacity: 1, y: 0 }}
                     transition={{ duration: 0.6, delay: 0.2 }}
                     viewport={{ once: true }}
                 >
                    <h4 className="font-semibold">Quick Links</h4>
                    <nav className="flex flex-col gap-2 text-sm">
                        {[
                            { href: "/login", label: "Login" },
                            { href: "#calculator", label: "ROI Calculator" },
                            { href: "#contact", label: "Request Demo" },
                            { href: "mailto:admin@bearsystems.co.in", label: "Partnership" }
                        ].map((item, index) => (
                            <motion.div
                                key={`footer-nav-${index}-${item.label}`}
                                initial={{ opacity: 0, x: -20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.4, delay: 0.1 + index * 0.1 }}
                                viewport={{ once: true }}
                            >
                                <Link href={item.href} className="text-muted-foreground hover:text-primary transition-colors">
                                    {item.label}
                                </Link>
                            </motion.div>
                        ))}
                    </nav>
                 </motion.div>
                 <motion.div 
                     className="space-y-4 lg:col-span-2"
                     initial={{ opacity: 0, y: 20 }}
                     whileInView={{ opacity: 1, y: 0 }}
                     transition={{ duration: 0.6, delay: 0.4 }}
                     viewport={{ once: true }}
                 >
                     <h4 className="font-semibold">Get Started</h4>
                     <p className="text-sm text-muted-foreground">Ready to revolutionize your HR operations?</p>
                     <motion.div
                         whileHover={{ scale: 1.02 }}
                         whileTap={{ scale: 0.98 }}
                     >
                         <Button asChild className="bg-primary hover:bg-primary/90 text-primary-foreground">
                            <a href="mailto:admin@bearsystems.co.in">
                                Contact for Access
                            </a>
                         </Button>
                     </motion.div>
                      <p className="text-xs text-muted-foreground">Response within 24 hours</p>
                 </motion.div>
            </div>
             <div className="border-t">
                <motion.div 
                    className="container flex flex-col gap-2 sm:flex-row py-4 items-center justify-between"
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    transition={{ duration: 0.6 }}
                    viewport={{ once: true }}
                >
                    <p className="text-xs text-muted-foreground">
                    &copy; {year} Bear Systems HRT. A proud product of BearSystems.co.in.
                    </p>
                    <nav className="flex gap-4 sm:gap-6">
                    <Link href="#" className="text-xs hover:underline underline-offset-4 hover:text-primary transition-colors">
                        Terms of Service
                    </Link>
                    <Link href="#" className="text-xs hover:underline underline-offset-4 hover:text-primary transition-colors">
                        Privacy
                    </Link>
                    </nav>
                </motion.div>
            </div>
        </footer>
    </div>
  );
}
