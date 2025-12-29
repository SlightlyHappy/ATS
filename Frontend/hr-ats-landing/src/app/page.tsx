import { Header } from '@/components/Header'
import { HeroSection } from '@/components/HeroSection'
import { AgentSystem } from '@/components/AgentSystem'
import { TechnicalFeatures } from '@/components/TechnicalFeatures'
import { CompetitiveAnalysis } from '@/components/CompetitiveAnalysis'
import { ROICalculator } from '@/components/ROICalculator'
import { Footer } from '@/components/Footer'

export default function Home() {
  return (
    <main className="min-h-screen bg-white">
      <Header />
      <HeroSection />
      <AgentSystem />
      <TechnicalFeatures />
      <CompetitiveAnalysis />
      <ROICalculator />
      <Footer />
    </main>
  )
}
