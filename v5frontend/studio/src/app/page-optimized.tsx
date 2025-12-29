import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AppLogo } from '@/components/shared/app-logo';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { Badge } from '@/components/ui/badge';

// Static data - no dynamic imports for performance
const agentFeatures = [
  {
    title: 'Technical Intelligence Agent',
    description: 'Advanced technical skill assessment and candidate evaluation through sophisticated AI-powered analysis.',
  },
  {
    title: 'Cultural Intelligence Agent', 
    description: 'Comprehensive cultural fit analysis ensuring optimal team integration and organizational alignment.',
  },
  {
    title: 'Legal Compliance Agent',
    description: 'Automated compliance monitoring with real-time updates for Indian labor laws and regulations.',
  },
  {
    title: 'Experience Intelligence Agent',
    description: 'Deep experience analysis and career trajectory evaluation for strategic hiring decisions.',
  }
];

const companyStats = [
  { value: '95%', label: 'Compliance Accuracy' },
  { value: '8.5x', label: 'Faster Screening' },
  { value: '90%', label: 'Cost Reduction' },
  { value: '24/7', label: 'Availability' }
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <AppLogo />
            <span className="font-bold text-xl">BearSystemsHRT©</span>
          </Link>
          <div className="flex items-center space-x-4">
            <Button asChild>
              <Link href="/admin/login">Enterprise Access</Link>
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-24 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <Badge variant="outline" className="mb-6">
            Agentic HR Intelligence Platform
          </Badge>
          
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            Revolutionary HR Intelligence
            <br />
            <span className="text-primary">for Indian Organizations</span>
          </h1>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Transform your recruitment process with autonomous AI agents. 
            Streamline hiring, ensure compliance, and make data-driven decisions 
            with our enterprise-grade platform.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg">
              <Link href="/admin/login">Get Started</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/admin/dashboard">View Demo</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 bg-muted/30">
        <div className="container mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {companyStats.map((stat, index) => (
              <div key={index}>
                <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground font-medium">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Autonomous Agent Intelligence
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Four specialized AI agents working together to revolutionize your recruitment process
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {agentFeatures.map((feature, index) => (
              <Card key={index} className="border border-border/40">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <div className="w-6 h-6 bg-primary rounded-sm"></div>
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24 px-4 bg-muted/30">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Enterprise Benefits
            </h2>
            <p className="text-lg text-muted-foreground">
              Built specifically for Indian organizations and compliance requirements
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <div className="w-8 h-8 bg-primary rounded-md"></div>
              </div>
              <h3 className="text-xl font-semibold mb-3">Compliance First</h3>
              <p className="text-muted-foreground">
                Automated compliance with Indian labor laws and industry regulations
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <div className="w-8 h-8 bg-primary rounded-md"></div>
              </div>
              <h3 className="text-xl font-semibold mb-3">Intelligent Screening</h3>
              <p className="text-muted-foreground">
                Advanced AI-powered candidate evaluation and technical assessment
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <div className="w-8 h-8 bg-primary rounded-md"></div>
              </div>
              <h3 className="text-xl font-semibold mb-3">Data Security</h3>
              <p className="text-muted-foreground">
                Enterprise-grade security with comprehensive data protection
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4">
        <div className="container mx-auto max-w-3xl text-center">
          <div className="border border-border/40 rounded-2xl p-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Ready to Transform Your HR Process?
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Join leading Indian organizations using BearSystemsHRT© for intelligent recruitment
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" asChild>
                <Link href="/admin/login">Start Enterprise Trial</Link>
              </Button>
              <Button variant="outline" size="lg" asChild>
                <Link href="mailto:enterprise@bearsystems.co.in">Contact Sales</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 px-4">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <AppLogo />
            <span className="font-bold text-lg">BearSystemsHRT©</span>
          </div>
          <p className="text-muted-foreground mb-4">
            Agentic HR Intelligence for Modern Organizations
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
            <Link href="/terms" className="hover:text-foreground transition-colors">Terms</Link>
            <Link href="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
            <Link href="mailto:support@bearsystems.co.in" className="hover:text-foreground transition-colors">Support</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
