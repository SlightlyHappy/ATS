"""
ROI Calculator Service - Calculate return on investment for prospects
and existing customers using the AI Resume Analysis platform.
"""
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
from app import db
from app.models.sales import ROICalculation

logger = logging.getLogger(__name__)

@dataclass
class ROIInput:
    """Input parameters for ROI calculation."""
    monthly_analyses: int
    hourly_rate: float
    time_saved_per_analysis: float = 2.0  # Default 2 hours saved per analysis
    current_process_cost: Optional[float] = None
    platform_cost_per_analysis: float = 2.0  # Default $2 per analysis

@dataclass
class ROIResult:
    """ROI calculation results."""
    monthly_time_savings: float  # Hours
    monthly_cost_savings: float  # USD
    platform_cost: float  # USD
    net_savings: float  # USD
    roi_percentage: float
    payback_period_days: float
    annual_savings: float
    three_year_savings: float

class ROICalculatorService:
    """Service for calculating ROI for prospects and customers."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_roi(self, roi_input: ROIInput, lead_id: Optional[str] = None) -> ROIResult:
        """
        Calculate comprehensive ROI for the AI Resume Analysis platform.
        
        Args:
            roi_input: Input parameters for calculation
            lead_id: Optional lead ID to save calculation
            
        Returns:
            ROIResult with all calculated metrics
        """
        try:
            # Calculate monthly time savings
            monthly_time_savings = roi_input.monthly_analyses * roi_input.time_saved_per_analysis
            
            # Calculate monthly cost savings
            monthly_cost_savings = monthly_time_savings * roi_input.hourly_rate
            
            # Calculate platform cost
            platform_cost = roi_input.monthly_analyses * roi_input.platform_cost_per_analysis
            
            # Add current process cost if provided
            if roi_input.current_process_cost:
                monthly_cost_savings += roi_input.current_process_cost
            
            # Calculate net savings
            net_savings = monthly_cost_savings - platform_cost
            
            # Calculate ROI percentage
            if platform_cost > 0:
                roi_percentage = (net_savings / platform_cost) * 100
            else:
                roi_percentage = 0
            
            # Calculate payback period
            if net_savings > 0:
                payback_period_days = (platform_cost / (net_savings / 30))
            else:
                payback_period_days = float('inf')
            
            # Calculate long-term savings
            annual_savings = net_savings * 12
            three_year_savings = annual_savings * 3
            
            result = ROIResult(
                monthly_time_savings=monthly_time_savings,
                monthly_cost_savings=monthly_cost_savings,
                platform_cost=platform_cost,
                net_savings=net_savings,
                roi_percentage=roi_percentage,
                payback_period_days=payback_period_days,
                annual_savings=annual_savings,
                three_year_savings=three_year_savings
            )
            
            # Save calculation if lead_id provided
            if lead_id:
                self._save_calculation(roi_input, result, lead_id)
            
            self.logger.info(f"ROI calculated: {roi_input.monthly_analyses} analyses -> "
                           f"{roi_percentage:.1f}% ROI, ${net_savings:.2f} monthly savings")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating ROI: {str(e)}")
            raise
    
    def _save_calculation(self, roi_input: ROIInput, result: ROIResult, lead_id: str):
        """Save ROI calculation to database."""
        try:
            calculation = ROICalculation(
                lead_id=lead_id,
                monthly_analyses=roi_input.monthly_analyses,
                time_saved_per_analysis=roi_input.time_saved_per_analysis,
                hourly_rate=roi_input.hourly_rate,
                current_process_cost=roi_input.current_process_cost,
                monthly_time_savings=result.monthly_time_savings,
                monthly_cost_savings=result.monthly_cost_savings,
                platform_cost=result.platform_cost,
                net_savings=result.net_savings,
                roi_percentage=result.roi_percentage,
                payback_period_days=result.payback_period_days,
                annual_savings=result.annual_savings,
                three_year_savings=result.three_year_savings,
                calculation_metadata={
                    'platform_cost_per_analysis': roi_input.platform_cost_per_analysis,
                    'calculation_date': datetime.utcnow().isoformat()
                }
            )
            
            db.session.add(calculation)
            db.session.commit()
            
            self.logger.info(f"ROI calculation saved for lead {lead_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving ROI calculation: {str(e)}")
            db.session.rollback()
    
    def get_industry_benchmarks(self, industry: Optional[str] = None) -> Dict:
        """
        Get industry-specific ROI benchmarks and comparisons.
        
        Args:
            industry: Industry type for specific benchmarks
            
        Returns:
            Dictionary with benchmark data
        """
        # Industry-specific benchmarks based on typical HR costs and efficiency
        benchmarks = {
            'recruiting': {
                'typical_hourly_rate': 65,
                'time_per_resume_review': 3.0,
                'monthly_volume_range': (50, 500),
                'efficiency_gain': 0.75,  # 75% time reduction
                'notes': 'Recruiting firms typically see highest ROI due to volume and specialist rates'
            },
            'hr_department': {
                'typical_hourly_rate': 45,
                'time_per_resume_review': 2.5,
                'monthly_volume_range': (20, 200),
                'efficiency_gain': 0.70,  # 70% time reduction
                'notes': 'Corporate HR departments benefit from consistency and reduced bias'
            },
            'consulting': {
                'typical_hourly_rate': 85,
                'time_per_resume_review': 2.0,
                'monthly_volume_range': (10, 100),
                'efficiency_gain': 0.65,  # 65% time reduction
                'notes': 'Consulting firms value speed and quality for client projects'
            },
            'startup': {
                'typical_hourly_rate': 55,
                'time_per_resume_review': 4.0,
                'monthly_volume_range': (5, 50),
                'efficiency_gain': 0.80,  # 80% time reduction
                'notes': 'Startups benefit most from automation due to limited HR resources'
            }
        }
        
        if industry and industry.lower() in benchmarks:
            return benchmarks[industry.lower()]
        
        # Return general benchmarks
        return {
            'typical_hourly_rate': 55,
            'time_per_resume_review': 2.5,
            'monthly_volume_range': (20, 200),
            'efficiency_gain': 0.70,
            'notes': 'General industry averages across all sectors'
        }
    
    def calculate_scenario_comparison(self, base_input: ROIInput) -> Dict:
        """
        Calculate ROI for multiple scenarios (conservative, realistic, optimistic).
        
        Args:
            base_input: Base calculation parameters
            
        Returns:
            Dictionary with scenario comparisons
        """
        scenarios = {}
        
        # Conservative scenario (50% of claimed benefits)
        conservative_input = ROIInput(
            monthly_analyses=base_input.monthly_analyses,
            hourly_rate=base_input.hourly_rate,
            time_saved_per_analysis=base_input.time_saved_per_analysis * 0.5,
            current_process_cost=base_input.current_process_cost,
            platform_cost_per_analysis=base_input.platform_cost_per_analysis
        )
        scenarios['conservative'] = self.calculate_roi(conservative_input)
        
        # Realistic scenario (base input)
        scenarios['realistic'] = self.calculate_roi(base_input)
        
        # Optimistic scenario (150% benefits + growth)
        optimistic_input = ROIInput(
            monthly_analyses=int(base_input.monthly_analyses * 1.5),  # Assume 50% growth
            hourly_rate=base_input.hourly_rate,
            time_saved_per_analysis=base_input.time_saved_per_analysis * 1.2,  # 20% more efficient
            current_process_cost=base_input.current_process_cost,
            platform_cost_per_analysis=base_input.platform_cost_per_analysis * 0.9  # Volume discount
        )
        scenarios['optimistic'] = self.calculate_roi(optimistic_input)
        
        return scenarios
    
    def generate_roi_report(self, roi_input: ROIInput, lead_id: Optional[str] = None) -> Dict:
        """
        Generate comprehensive ROI report with multiple scenarios and benchmarks.
        
        Args:
            roi_input: Input parameters
            lead_id: Optional lead ID
            
        Returns:
            Complete ROI report dictionary
        """
        try:
            # Calculate main ROI
            main_result = self.calculate_roi(roi_input, lead_id)
            
            # Calculate scenario comparisons
            scenarios = self.calculate_scenario_comparison(roi_input)
            
            # Get industry benchmarks
            benchmarks = self.get_industry_benchmarks()
            
            # Calculate break-even analysis
            break_even_analyses = int(roi_input.platform_cost_per_analysis * 30 / 
                                    (roi_input.time_saved_per_analysis * roi_input.hourly_rate))
            
            report = {
                'input_parameters': {
                    'monthly_analyses': roi_input.monthly_analyses,
                    'hourly_rate': roi_input.hourly_rate,
                    'time_saved_per_analysis': roi_input.time_saved_per_analysis,
                    'platform_cost_per_analysis': roi_input.platform_cost_per_analysis
                },
                'main_results': {
                    'monthly_savings': main_result.net_savings,
                    'roi_percentage': main_result.roi_percentage,
                    'payback_period_days': main_result.payback_period_days,
                    'annual_savings': main_result.annual_savings,
                    'three_year_savings': main_result.three_year_savings
                },
                'scenarios': {
                    'conservative': {
                        'monthly_savings': scenarios['conservative'].net_savings,
                        'roi_percentage': scenarios['conservative'].roi_percentage
                    },
                    'realistic': {
                        'monthly_savings': scenarios['realistic'].net_savings,
                        'roi_percentage': scenarios['realistic'].roi_percentage
                    },
                    'optimistic': {
                        'monthly_savings': scenarios['optimistic'].net_savings,
                        'roi_percentage': scenarios['optimistic'].roi_percentage
                    }
                },
                'benchmarks': benchmarks,
                'break_even_analysis': {
                    'monthly_analyses_needed': break_even_analyses,
                    'current_vs_breakeven': roi_input.monthly_analyses / max(break_even_analyses, 1)
                },
                'recommendations': self._generate_recommendations(main_result, roi_input),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating ROI report: {str(e)}")
            raise
    
    def _generate_recommendations(self, result: ROIResult, input_params: ROIInput) -> List[str]:
        """Generate actionable recommendations based on ROI results."""
        recommendations = []
        
        if result.roi_percentage > 200:
            recommendations.append("Excellent ROI! Consider upgrading to higher volume tiers for additional savings.")
            recommendations.append("This platform will pay for itself in less than a month.")
        elif result.roi_percentage > 100:
            recommendations.append("Strong positive ROI. The platform provides significant value.")
            recommendations.append(f"You'll break even in {result.payback_period_days:.1f} days.")
        elif result.roi_percentage > 50:
            recommendations.append("Positive ROI with good long-term value.")
            recommendations.append("Consider starting with a pilot program to validate benefits.")
        else:
            recommendations.append("ROI is lower than typical. Consider the following optimizations:")
            recommendations.append("- Increase analysis volume to achieve better economies of scale")
            recommendations.append("- Focus on higher-value roles where time savings matter most")
        
        # Volume-based recommendations
        if input_params.monthly_analyses < 20:
            recommendations.append("Consider batching resume reviews to maximize efficiency gains.")
        elif input_params.monthly_analyses > 200:
            recommendations.append("Contact us for enterprise pricing and additional volume discounts.")
        
        return recommendations
