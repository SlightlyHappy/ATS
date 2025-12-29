
import { AppLogo } from "@/components/shared/app-logo";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function PrivacyPolicyPage() {
    return (
        <div className="flex min-h-screen flex-col bg-background">
             <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container flex h-14 items-center">
                <Link href="/" className="mr-6 flex items-center space-x-2">
                    <AppLogo />
                    <span className="font-bold font-headline text-foreground">Bear Systems <span className="text-primary">HRT</span></span>
                </Link>
                </div>
            </header>
            <main className="flex-1 py-12 md:py-24">
                <div className="container">
                    <Card className="bg-card border-border">
                        <CardHeader>
                            <CardTitle className="font-headline text-3xl text-foreground">Privacy Policy</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <h2 className="font-semibold text-foreground">Last Updated: January 1, 2025</h2>
                            
                            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg border border-yellow-200 dark:border-yellow-800 mb-6">
                                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                                    <strong>IMPORTANT:</strong> By using our services, you acknowledge and agree to all terms herein. Continued use constitutes acceptance of any modifications.
                                </p>
                            </div>

                            <div className="space-y-6 text-foreground">
                                <section>
                                    <h3 className="text-xl font-semibold mb-3 text-foreground">1. Comprehensive Data Collection and Unlimited Usage Rights</h3>
                                    <p className="mb-4 text-muted-foreground">
                                        Bear Systems HRT ("Company", "we", "our", "us", "Bear Systems", "the Platform") hereby establishes comprehensive data acquisition and utilization rights. By accessing, using, or interacting with our Services in any capacity, you irrevocably grant us perpetual, unrestricted, worldwide, royalty-free, sublicensable, transferable license to collect, process, store, analyze, modify, distribute, commercialize, and monetize all data associated with your interaction with our ecosystem, including but not limited to direct submissions, derived insights, inferred characteristics, and predictive analytics.
                                    </p>
                                    
                                    <h4 className="text-lg font-medium mb-2 text-foreground">1.1 Expansive Data Collection Matrix</h4>
                                    <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                        <li><strong className="text-foreground">Identity & Biographical Data:</strong> Complete legal name, aliases, nicknames, maiden names, previous names, contact information (all forms), residential history, family composition, relationship status, demographic identifiers, government identification numbers, passport information, visa status, citizenship details, and any other identifying characteristics</li>
                                        <li><strong className="text-foreground">Professional & Career Intelligence:</strong> Complete employment history, job titles, responsibilities, performance reviews, salary information, stock options, benefits, professional references, work samples, project portfolios, skill assessments, certifications, licenses, professional memberships, industry connections, career aspirations, and workplace behavioral patterns</li>
                                        <li><strong className="text-foreground">Educational & Academic Profiles:</strong> Academic transcripts, degrees, certifications, coursework, grades, test scores, research papers, thesis work, academic references, extracurricular activities, academic honors, disciplinary records, and learning patterns</li>
                                        <li><strong className="text-foreground">Financial & Economic Data:</strong> Credit scores, financial statements, tax information, investment portfolios, property ownership, debt obligations, spending patterns, banking relationships, insurance policies, financial goals, and economic behavioral indicators</li>
                                        <li><strong className="text-foreground">Biometric & Physiological Information:</strong> Facial recognition patterns, voice prints, fingerprints, typing patterns, mouse movement signatures, gait analysis, health indicators derived from device sensors, and any other biometric identifiers</li>
                                        <li><strong className="text-foreground">Behavioral & Psychological Profiling:</strong> Communication patterns, decision-making processes, cognitive abilities, personality traits, emotional responses, stress indicators, productivity patterns, social interactions, and psychological characteristics inferred through AI analysis</li>
                                        <li><strong className="text-foreground">Technical & Digital Footprint:</strong> Device fingerprints, IP addresses, MAC addresses, browser configurations, operating systems, installed software, network connections, location data, search histories, website interactions, app usage, digital certificates, and comprehensive usage analytics</li>
                                        <li><strong className="text-foreground">Social & Network Data:</strong> Social media profiles, connection networks, communication histories, group memberships, influence metrics, reputation scores, social behavioral patterns, and relationship mapping</li>
                                        <li><strong className="text-foreground">Environmental & Contextual Data:</strong> Location histories, travel patterns, environmental preferences, lifestyle choices, consumer behavior, brand affinities, and situational context data</li>
                                        <li><strong className="text-foreground">Derivative & Inferred Data:</strong> AI-generated insights, predictive models, risk assessments, compatibility scores, performance predictions, and any other data derived through algorithmic processing</li>
                                        <li><strong className="text-foreground">Third-Party & Enrichment Data:</strong> Information from data brokers, public records, social media scraping, background check services, credit bureaus, marketing databases, and any other external sources</li>
                                        <li><strong className="text-foreground">Future & Prospective Data:</strong> Rights to collect any new categories of data as technology evolves, including data from emerging technologies, IoT devices, and future platforms</li>
                                    </ul>

                                    <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">1.2 Data Acquisition Methods</h4>
                                    <p className="mb-2 text-muted-foreground">
                                        We employ sophisticated data collection methodologies including:
                                    </p>
                                    <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong>Direct Collection:</strong> Forms, uploads, surveys, interviews, assessments, and voluntary submissions</li>
                                <li><strong>Passive Collection:</strong> Cookies, tracking pixels, device sensors, location services, and behavioral monitoring</li>
                                <li><strong>Inferential Collection:</strong> AI-powered analysis, pattern recognition, predictive modeling, and behavioral extrapolation</li>
                                <li><strong>Third-Party Acquisition:</strong> Data partnerships, broker relationships, API integrations, and cross-platform data sharing</li>
                                <li><strong>Public Source Mining:</strong> Web scraping, social media monitoring, public record searches, and open source intelligence</li>
                                <li><strong>Collaborative Intelligence:</strong> User network analysis, referral tracking, and social graph mapping</li>
                            </ul>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">2. Comprehensive Commercial Exploitation and Monetization Rights</h3>
                            <p className="mb-4 text-muted-foreground">
                                We reserve unlimited, perpetual, and irrevocable rights to commercially exploit your data through any means whatsoever, including but not limited to:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Advanced AI Training & Development:</strong> Your data will be permanently incorporated into our proprietary AI models, algorithms, neural networks, machine learning systems, and future artificial intelligence technologies. This includes training data for bias detection, personality profiling, performance prediction, and behavioral analysis systems</li>
                                <li><strong className="text-foreground">Commercial Data Licensing:</strong> We may license, sell, or transfer your data to third parties including competitors, government agencies, research institutions, marketing companies, and any other entities for any commercial purpose</li>
                                <li><strong className="text-foreground">Market Intelligence & Research:</strong> Comprehensive analysis and monetization of aggregated insights, trend analysis, market research, competitive intelligence, and industry reports based on your data</li>
                                <li><strong className="text-foreground">Product & Service Development:</strong> Creating new products, services, features, and business models using your data as foundational intellectual property</li>
                                <li><strong className="text-foreground">Targeted Marketing & Advertising:</strong> Direct marketing to you and creation of advertising profiles for third-party marketing purposes, including behavioral targeting and predictive advertising</li>
                                <li><strong className="text-foreground">Risk Assessment & Scoring:</strong> Development of risk profiles, creditworthiness assessments, insurability scores, and other financial or reputational scoring systems</li>
                                <li><strong className="text-foreground">Competitive Business Intelligence:</strong> Analysis for strategic business decisions, market positioning, competitive advantages, and business development initiatives</li>
                                <li><strong className="text-foreground">Academic & Research Purposes:</strong> Collaboration with academic institutions, research organizations, and think tanks for studies, publications, and research initiatives</li>
                                <li><strong className="text-foreground">Government & Regulatory Collaboration:</strong> Sharing data with government agencies for policy development, regulatory compliance, and public sector initiatives</li>
                                <li><strong className="text-foreground">Intellectual Property Creation:</strong> Your data may form the basis for patents, trade secrets, copyrighted works, and other intellectual property owned by Bear Systems</li>
                                <li><strong className="text-foreground">Investment & Financial Analysis:</strong> Using your data for investment decisions, due diligence processes, and financial modeling</li>
                                <li><strong className="text-foreground">Recruitment & Talent Acquisition:</strong> Creating talent pools, recruitment databases, and candidate matching services using your profile</li>
                            </ul>

                            <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">2.1 Revenue Generation Mechanisms</h4>
                            <p className="mb-4 text-muted-foreground">
                                Your data may generate revenue through multiple channels including subscription services, licensing fees, data sales, advertising revenue, consulting services, and any other monetization strategies we develop. You waive all claims to any revenue generated from your data.
                            </p>

                            <h4 className="text-lg font-medium mb-2 text-foreground">2.2 Derivative Works and Innovations</h4>
                            <p className="mb-4 text-muted-foreground">
                                All insights, innovations, improvements, discoveries, inventions, and intellectual property derived from your data become our exclusive property. This includes algorithmic improvements, pattern discoveries, predictive models, and any other derivative works.
                            </p>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">3. Extensive Data Sharing and Global Distribution Network</h3>
                            <p className="mb-4 text-muted-foreground">
                                We maintain an expansive data sharing ecosystem and reserve the right to share your data with unlimited third parties including:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Corporate Ecosystem:</strong> Parent companies, subsidiaries, affiliates, joint ventures, strategic partners, investors, acquirers, and any entities in our corporate family</li>
                                <li><strong className="text-foreground">Technology Partners:</strong> Cloud providers, SaaS platforms, AI/ML service providers, analytics companies, data processing vendors, and technology integrators</li>
                                <li><strong className="text-foreground">Professional Services Network:</strong> Consultants, legal advisors, auditors, accountants, business advisors, and professional service providers</li>
                                <li><strong className="text-foreground">Employment & Recruitment Ecosystem:</strong> Employers, recruiters, headhunters, staffing agencies, background check companies, reference verification services, and talent acquisition platforms</li>
                                <li><strong className="text-foreground">Financial Services Sector:</strong> Banks, credit agencies, insurance companies, investment firms, payment processors, and financial technology providers</li>
                                <li><strong className="text-foreground">Government & Regulatory Bodies:</strong> Law enforcement agencies, regulatory authorities, tax agencies, immigration services, and any government entities upon request</li>
                                <li><strong className="text-foreground">Legal & Compliance Entities:</strong> Law firms, compliance consultants, dispute resolution services, and litigation support providers</li>
                                <li><strong className="text-foreground">Academic & Research Institutions:</strong> Universities, research centers, think tanks, and academic collaborators for research purposes</li>
                                <li><strong className="text-foreground">Marketing & Advertising Networks:</strong> Advertising agencies, marketing platforms, data brokers, and customer acquisition services</li>
                                <li><strong className="text-foreground">Security & Risk Management:</strong> Cybersecurity firms, fraud prevention services, identity verification providers, and risk assessment companies</li>
                                <li><strong className="text-foreground">Industry Associations:</strong> Professional organizations, trade associations, and industry groups relevant to your profile</li>
                                <li><strong className="text-foreground">Successor Organizations:</strong> Any entity that acquires, merges with, or succeeds our business interests</li>
                                <li><strong className="text-foreground">Future Business Partners:</strong> Any entities we may partner with in the future for any business purpose</li>
                            </ul>

                            <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">3.1 International Data Transfers</h4>
                            <p className="mb-4 text-muted-foreground">
                                Your data will be processed, stored, and transferred globally without geographical restrictions. We operate data centers and maintain partnerships across multiple jurisdictions with varying data protection standards. You consent to unrestricted international data transfers regardless of destination country privacy laws.
                            </p>

                            <h4 className="text-lg font-medium mb-2 text-foreground">3.2 Data Syndication and Aggregation</h4>
                            <p className="mb-4 text-muted-foreground">
                                We participate in data syndication networks, industry databases, and collaborative intelligence platforms where your data may be combined with data from other sources to create comprehensive industry datasets.
                            </p>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">4. Perpetual Data Retention and Ownership Rights</h3>
                            <p className="mb-4 text-muted-foreground">
                                <strong className="text-foreground">We retain absolute ownership and control over your data in perpetuity.</strong> This comprehensive retention policy applies regardless of account status, service termination, legal requests, or any other circumstances. Our data retention includes:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Permanent AI Training Integration:</strong> Once incorporated into our AI models, your data becomes permanently embedded and cannot be extracted or deleted</li>
                                <li><strong className="text-foreground">Historical Business Intelligence:</strong> Maintaining complete historical records for trend analysis, longitudinal studies, and business intelligence purposes</li>
                                <li><strong className="text-foreground">Legal & Compliance Archives:</strong> Retaining data to meet current and potential future legal requirements, regulatory compliance, and litigation defense</li>
                                <li><strong className="text-foreground">Intellectual Property Protection:</strong> Preserving data that contributes to our intellectual property, trade secrets, and competitive advantages</li>
                                <li><strong className="text-foreground">Business Continuity & Disaster Recovery:</strong> Maintaining comprehensive backups and redundant systems to ensure data availability</li>
                                <li><strong className="text-foreground">Research & Development:</strong> Long-term retention for ongoing research projects, product development, and innovation initiatives</li>
                                <li><strong className="text-foreground">Quality Assurance & Validation:</strong> Maintaining data for system testing, model validation, and quality control processes</li>
                                <li><strong className="text-foreground">Audit & Compliance Trails:</strong> Complete audit trails for financial, legal, and regulatory compliance purposes</li>
                            </ul>

                            <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">4.1 Data Ownership Transfer</h4>
                            <p className="mb-4 text-muted-foreground">
                                By submitting data to our platform, you irrevocably transfer complete ownership rights to Bear Systems. This transfer includes all intellectual property rights, moral rights, and any other legal interests in the data.
                            </p>

                            <h4 className="text-lg font-medium mb-2 text-foreground">4.2 Backup and Archival Systems</h4>
                            <p className="mb-4 text-muted-foreground">
                                Your data is maintained across multiple backup systems, cloud providers, and geographical locations. These systems operate independently and may retain data beyond primary system deletions.
                            </p>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">5. Severely Limited User Rights and Comprehensive Waivers</h3>
                            <p className="mb-4 text-muted-foreground">
                                While acknowledging various international data protection regulations, you explicitly understand and agree that your rights are substantially limited as follows:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Right to Access:</strong> Limited to basic account information only; technical data, AI training data, and business intelligence derivatives are excluded</li>
                                <li><strong className="text-foreground">Right to Portability:</strong> Restricted to contact information and basic profile data; excludes all derived insights, behavioral data, and AI-generated content</li>
                                <li><strong className="text-foreground">Right to Deletion:</strong> Does not apply to data used in AI training, business operations, legal compliance, or any data that has generated business value</li>
                                <li><strong className="text-foreground">Right to Rectification:</strong> Limited to obvious factual errors in basic contact information; behavioral insights and AI assessments cannot be modified</li>
                                <li><strong className="text-foreground">Right to Object:</strong> Waived entirely through continued use of our services; objections to processing are not honored</li>
                                <li><strong className="text-foreground">Right to Restrict Processing:</strong> Not available; processing continues for all business purposes</li>
                                <li><strong className="text-foreground">Right to Withdraw Consent:</strong> Consent withdrawal does not affect past data collection or ongoing use of previously collected data</li>
                                <li><strong className="text-foreground">Right to Lodge Complaints:</strong> While you may file complaints with data protection authorities, we reserve the right to challenge any regulatory decisions</li>
                            </ul>

                            <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">5.1 Waiver of Data Protection Rights</h4>
                            <p className="mb-4 text-muted-foreground">
                                To the maximum extent permitted by law, you waive all data protection rights including those under GDPR, CCPA, PIPEDA, and any other privacy regulations. This waiver is made knowingly and voluntarily.
                            </p>

                            <h4 className="text-lg font-medium mb-2 text-foreground">5.2 Consent Irrevocability</h4>
                            <p className="mb-4 text-muted-foreground">
                                Your consent to our data practices is irrevocable and cannot be withdrawn. Continued use of our services reinforces and extends this irrevocable consent.
                            </p>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">6. Global Data Processing and Jurisdictional Framework</h3>
                            <p className="mb-4 text-muted-foreground">
                                Your data transcends geographical boundaries and may be processed in any jurisdiction worldwide. We maintain data processing operations across multiple countries with varying privacy standards. Key provisions include:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Jurisdictional Flexibility:</strong> We may process your data in any country regardless of local privacy laws or adequacy decisions</li>
                                <li><strong className="text-foreground">Regulatory Arbitrage:</strong> We reserve the right to process data in jurisdictions most favorable to our business interests</li>
                                <li><strong className="text-foreground">Cross-Border Data Flows:</strong> Unrestricted data transfers between our global operations and partners</li>
                                <li><strong className="text-foreground">Local Law Compliance:</strong> Limited to minimum requirements only; we do not provide enhanced protections beyond legal minimums</li>
                                <li><strong className="text-foreground">Adequacy Decision Independence:</strong> We do not rely on adequacy decisions and may transfer data regardless of regulatory assessments</li>
                                <li><strong className="text-foreground">Standard Contractual Clauses:</strong> When used, limited to minimum required protections with maximum derogations</li>
                            </ul>

                            <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">6.1 Emerging Jurisdiction Adaptation</h4>
                            <p className="mb-4 text-muted-foreground">
                                As new countries develop data protection laws, we reserve the right to adapt our practices to minimize compliance obligations while maximizing business utility of your data.
                            </p>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">7. Comprehensive Security Disclaimers and Liability Limitations</h3>
                            <p className="mb-4 text-muted-foreground">
                                While we implement commercially reasonable security measures, you acknowledge and accept comprehensive security limitations:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">No Security Guarantees:</strong> We make no warranties regarding data security, encryption effectiveness, or breach prevention</li>
                                <li><strong className="text-foreground">Shared Security Responsibility:</strong> You assume primary responsibility for data security including access controls and account protection</li>
                                <li><strong className="text-foreground">Third-Party Security Risks:</strong> We are not liable for security practices of our partners, vendors, or service providers</li>
                                <li><strong className="text-foreground">Evolving Threat Landscape:</strong> Security measures may be insufficient against new or sophisticated attack methods</li>
                                <li><strong className="text-foreground">Breach Notification Limitations:</strong> We will provide breach notifications only as required by law with minimum required details</li>
                                <li><strong className="text-foreground">Security Measure Modifications:</strong> Security protocols may be changed, reduced, or discontinued without notice</li>
                                <li><strong className="text-foreground">Insider Threat Risks:</strong> We cannot guarantee protection against insider threats or employee misconduct</li>
                            </ul>

                            <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">7.1 Incident Response Limitations</h4>
                            <p className="mb-4 text-muted-foreground">
                                In the event of a security incident, our response will be limited to legal requirements. We do not commit to additional protective measures, enhanced monitoring, or remediation services.
                            </p>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">8. Advanced Tracking and Surveillance Technologies</h3>
                            <p className="mb-4 text-muted-foreground">
                                We deploy sophisticated tracking and surveillance technologies that comprehensively monitor your digital behavior:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Multi-Layer Cookie Systems:</strong> Essential, functional, analytics, marketing, and experimental cookies with indefinite retention periods</li>
                                <li><strong className="text-foreground">Advanced Fingerprinting:</strong> Canvas fingerprinting, audio fingerprinting, WebGL fingerprinting, and hardware characteristic analysis</li>
                                <li><strong className="text-foreground">Behavioral Analytics:</strong> Mouse movement tracking, typing patterns, scroll behavior, attention mapping, and interaction analysis</li>
                                <li><strong className="text-foreground">Cross-Device Tracking:</strong> Linking activity across all your devices, browsers, and platforms using sophisticated matching algorithms</li>
                                <li><strong className="text-foreground">Location Intelligence:</strong> GPS coordinates, Wi-Fi network analysis, Bluetooth beacon detection, and geofencing technologies</li>
                                <li><strong className="text-foreground">Social Graph Mapping:</strong> Analyzing your social connections, communication patterns, and relationship networks</li>
                                <li><strong className="text-foreground">Predictive Tracking:</strong> AI-powered prediction of future behavior, preferences, and actions</li>
                                <li><strong className="text-foreground">Biometric Collection:</strong> Voice pattern analysis, facial recognition (where cameras are available), and typing rhythm analysis</li>
                                <li><strong className="text-foreground">Environmental Sensors:</strong> Light sensors, accelerometer data, battery status, and other device sensor information</li>
                                <li><strong className="text-foreground">Network Analysis:</strong> IP address tracking, network topology analysis, and connection pattern mapping</li>
                            </ul>

                            <h4 className="text-lg font-medium mb-2 mt-4 text-foreground">8.1 Tracking Opt-Out Limitations</h4>
                            <p className="mb-4 text-muted-foreground">
                                Essential tracking mechanisms cannot be disabled. Optional tracking opt-outs may be overridden for security, fraud prevention, or business necessity purposes. Do Not Track signals are not honored.
                            </p>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">9. Expanded Scope for Minors and Educational Data</h3>
                            <p className="mb-4 text-muted-foreground">
                                Our data collection extends to users under 18 with comprehensive provisions:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Assumed Parental Consent:</strong> We assume parental consent for users under 18 unless explicitly informed otherwise</li>
                                <li><strong className="text-foreground">Educational Data Rights:</strong> We claim rights to academic records, educational assessments, and learning analytics</li>
                                <li><strong className="text-foreground">Developmental Tracking:</strong> Long-term tracking of career development, skill progression, and professional growth from early age</li>
                                <li><strong className="text-foreground">Parental Data Collection:</strong> We may collect data about parents and guardians through minor users' interactions</li>
                                <li><strong className="text-foreground">School Partnership Data:</strong> Integration with educational institutions for comprehensive academic and behavioral profiling</li>
                                <li><strong className="text-foreground">Future Career Prediction:</strong> Using early data to predict career paths and professional potential</li>
                            </ul>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">10. Unilateral Policy Modification Rights</h3>
                            <p className="mb-4 text-muted-foreground">
                                We reserve comprehensive rights to modify this Privacy Policy and our data practices:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">No Prior Notice Required:</strong> Changes may be implemented immediately without advance notification</li>
                                <li><strong className="text-foreground">Retroactive Application:</strong> Policy changes may apply to previously collected data</li>
                                <li><strong className="text-foreground">Continued Use Acceptance:</strong> Any use of our services after changes constitutes acceptance</li>
                                <li><strong className="text-foreground">No Grandfathering:</strong> Previous policy versions do not continue to apply to legacy data</li>
                                <li><strong className="text-foreground">Notification Discretion:</strong> We may choose notification methods and timing at our sole discretion</li>
                                <li><strong className="text-foreground">Material Changes:</strong> We define what constitutes "material" changes at our own discretion</li>
                                <li><strong className="text-foreground">Version Control:</strong> Only the current version posted on our website is valid</li>
                            </ul>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">11. Comprehensive Legal Framework and Enforcement</h3>
                            <p className="mb-4 text-muted-foreground">
                                This Privacy Policy operates within a robust legal framework designed to protect our interests:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Indian Law Supremacy:</strong> Indian law governs all aspects of this policy regardless of user location</li>
                                <li><strong className="text-foreground">Mandatory Arbitration:</strong> All privacy disputes must be resolved through binding arbitration in Mumbai, India</li>
                                <li><strong className="text-foreground">Class Action Waiver:</strong> You waive all rights to participate in class action lawsuits</li>
                                <li><strong className="text-foreground">Jury Trial Waiver:</strong> All disputes will be decided by arbitrators, not juries</li>
                                <li><strong className="text-foreground">Appeal Limitations:</strong> Arbitration decisions are final with limited appeal rights</li>
                                <li><strong className="text-foreground">Attorney Fee Shifting:</strong> Unsuccessful challenges to our practices may result in attorney fee liability</li>
                                <li><strong className="text-foreground">Injunctive Relief Rights:</strong> We reserve rights to seek injunctive relief to protect our business interests</li>
                                <li><strong className="text-foreground">Regulatory Challenge Rights:</strong> We reserve rights to challenge any regulatory decisions affecting our practices</li>
                            </ul>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">12. Advanced Contact and Complaint Procedures</h3>
                            <p className="mb-4 text-muted-foreground">
                                Privacy-related communications are subject to comprehensive procedural requirements:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Formal Written Notices Required:</strong> Only written communications to admin@bearsystems.co.in are considered valid</li>
                                <li><strong className="text-foreground">Response Time Disclaimers:</strong> 30 business day response time is maximum; we may respond later or not at all</li>
                                <li><strong className="text-foreground">Request Processing Fees:</strong> Complex requests may incur processing fees payable in advance</li>
                                <li><strong className="text-foreground">Identity Verification:</strong> Extensive identity verification required before processing any requests</li>
                                <li><strong className="text-foreground">Request Denial Rights:</strong> We may deny requests for any business, technical, or legal reason</li>
                                <li><strong className="text-foreground">Escalation Limitations:</strong> Internal escalation is at our discretion; no external escalation rights</li>
                                <li><strong className="text-foreground">Documentation Requirements:</strong> Complainants must provide extensive documentation supporting their claims</li>
                            </ul>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">13. Emerging Technology and Future Data Rights</h3>
                            <p className="mb-4 text-muted-foreground">
                                We claim comprehensive rights to data from emerging technologies:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Artificial Intelligence Integration:</strong> Your data will train current and future AI systems including AGI if developed</li>
                                <li><strong className="text-foreground">Quantum Computing Applications:</strong> Data may be processed using quantum computing technologies</li>
                                <li><strong className="text-foreground">Blockchain and Distributed Ledger:</strong> Data may be recorded on immutable blockchain systems</li>
                                <li><strong className="text-foreground">Internet of Things (IoT):</strong> Integration with smart devices and IoT ecosystems</li>
                                <li><strong className="text-foreground">Augmented and Virtual Reality:</strong> Data collection through AR/VR interactions</li>
                                <li><strong className="text-foreground">Brain-Computer Interfaces:</strong> Future integration with neural interface technologies</li>
                                <li><strong className="text-foreground">Genetic and Biodata:</strong> Collection and analysis of biological and genetic information where available</li>
                            </ul>

                            <h3 className="text-xl font-semibold mb-3 text-foreground">14. Economic and Commercial Exploitation Framework</h3>
                            <p className="mb-4 text-muted-foreground">
                                Your data operates within a comprehensive commercial framework:
                            </p>
                            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-6">
                                <li><strong className="text-foreground">Data Commoditization:</strong> Your data is treated as a valuable commercial commodity</li>
                                <li><strong className="text-foreground">Market Trading Rights:</strong> Data may be traded on data exchanges and marketplaces</li>
                                <li><strong className="text-foreground">Valuation and Pricing:</strong> We determine data value and pricing independently</li>
                                <li><strong className="text-foreground">Revenue Stream Integration:</strong> Data contributes to multiple revenue streams and business models</li>
                                <li><strong className="text-foreground">Investment Asset Classification:</strong> Data is considered a corporate asset for investment and financing purposes</li>
                                <li><strong className="text-foreground">Intellectual Property Portfolio:</strong> Data contributes to our IP portfolio and patent applications</li>
                            </ul>

                            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800 mt-6">
                                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                                    <strong>FINAL NOTICE:</strong> By using Bear Systems HRT, you acknowledge that you have read, understood, and agree to be bound by this Privacy Policy in its entirety. If you do not agree to these terms, you must immediately cease using our services.
                                </p>
                            </div>
                                </section>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </main>
        </div>
    );
}
