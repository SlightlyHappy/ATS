"""
Enhanced Market Context and Realistic Scoring Configuration
Provides real-time market data, benchmarks, and scoring parameters for realistic resume analysis.
Integration from Salvage backend with enhanced market intelligence.
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import statistics
import json
from dataclasses import dataclass

from config import Config

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Market context data for realistic scoring."""
    role_type: str
    location: str
    experience_level: str
    skill_demand: Dict[str, float]  # skill -> demand score (0-1)
    salary_range: Tuple[int, int]
    market_saturation: float  # 0-1, higher means more competitive
    years_experience_benchmark: Dict[str, int]  # level -> typical years
    trending_skills: List[str]
    declining_skills: List[str]
    competitiveness_score: float  # 0-1, higher means more competitive market

class MarketDataProvider:
    """Enhanced provider for real-time market data and realistic scoring benchmarks."""
    
    def __init__(self, config: Config):
        self.config = config
        self.market_data = self._load_market_data()
        self.skill_market_data = self._load_enhanced_skill_market_data()
        self.historical_data = {}
        self.last_update = datetime.now()
        self.update_frequency = timedelta(hours=6)  # Update every 6 hours
        
    def _load_market_data(self) -> Dict[str, Any]:
        """Load comprehensive market data for different roles with enhanced metrics."""
        return {
            "software_engineer": {
                "demand_level": 0.9,
                "market_saturation": 0.7,
                "growth_rate": 0.15,
                "competitiveness_score": 0.8,
                "salary_ranges": {
                    "junior": (70000, 120000),
                    "mid": (120000, 180000),
                    "senior": (180000, 300000),
                    "principal": (250000, 450000)
                },
                "experience_benchmarks": {
                    "junior": {"min_years": 0, "max_years": 2, "typical_years": 1},
                    "mid": {"min_years": 2, "max_years": 5, "typical_years": 3.5},
                    "senior": {"min_years": 5, "max_years": 10, "typical_years": 7},
                    "principal": {"min_years": 8, "max_years": 15, "typical_years": 10}
                },
                "trending_skills": ["python", "react", "aws", "kubernetes", "machine learning", "typescript"],
                "declining_skills": ["jquery", "php", "flash", "legacy technologies"],
                "hot_skills": ["ai/ml", "cloud architecture", "devops", "microservices"],
                "saturated_skills": ["html", "css", "basic javascript"],
                "high_demand_locations": ["San Francisco", "New York", "Seattle", "Austin", "Boston"],
                "skill_premiums": {  # Additional value for having these skills
                    "machine learning": 1.2,
                    "kubernetes": 1.15,
                    "aws architect": 1.25,
                    "system design": 1.1
                }
            },
            
            "product_manager": {
                "demand_level": 0.8,
                "market_saturation": 0.8,
                "growth_rate": 0.12,
                "competitiveness_score": 0.85,
                "salary_ranges": {
                    "junior": (80000, 130000),
                    "mid": (130000, 200000),
                    "senior": (200000, 350000),
                    "director": (300000, 500000)
                },
                "experience_benchmarks": {
                    "junior": {"min_years": 0, "max_years": 3, "typical_years": 2},
                    "mid": {"min_years": 3, "max_years": 7, "typical_years": 5},
                    "senior": {"min_years": 7, "max_years": 12, "typical_years": 9},
                    "director": {"min_years": 10, "max_years": 20, "typical_years": 14}
                },
                "trending_skills": ["data analysis", "user research", "ai product management", "growth"],
                "declining_skills": ["traditional marketing", "waterfall methodology"],
                "hot_skills": ["user research", "data analysis", "sql", "roadmapping", "a/b testing"],
                "saturated_skills": ["agile", "scrum", "communication"],
                "high_demand_locations": ["San Francisco", "New York", "Seattle", "Los Angeles"],
                "skill_premiums": {
                    "data analysis": 1.15,
                    "user research": 1.1,
                    "growth hacking": 1.2,
                    "ai/ml knowledge": 1.25
                }
            },
            
            "data_scientist": {
                "demand_level": 0.85,
                "market_saturation": 0.6,
                "growth_rate": 0.20,
                "competitiveness_score": 0.75,
                "salary_ranges": {
                    "junior": (90000, 140000),
                    "mid": (140000, 200000),
                    "senior": (200000, 320000),
                    "principal": (280000, 450000)
                },
                "experience_benchmarks": {
                    "junior": {"min_years": 0, "max_years": 2, "typical_years": 1},
                    "mid": {"min_years": 2, "max_years": 5, "typical_years": 3},
                    "senior": {"min_years": 5, "max_years": 10, "typical_years": 7},
                    "principal": {"min_years": 8, "max_years": 15, "typical_years": 10}
                },
                "trending_skills": ["llm", "generative ai", "mlops", "pytorch", "transformers"],
                "declining_skills": ["basic statistics", "excel-only analysis"],
                "hot_skills": ["machine learning", "deep learning", "pytorch", "tensorflow", "mlops"],
                "saturated_skills": ["excel", "basic python", "basic sql"],
                "high_demand_locations": ["San Francisco", "New York", "Boston", "Seattle", "Austin"],
                "skill_premiums": {
                    "deep learning": 1.3,
                    "mlops": 1.25,
                    "llm/generative ai": 1.4,
                    "computer vision": 1.2
                }
            },
            
            "designer": {
                "demand_level": 0.7,
                "market_saturation": 0.75,
                "growth_rate": 0.10,
                "competitiveness_score": 0.78,
                "salary_ranges": {
                    "junior": (60000, 100000),
                    "mid": (100000, 150000),
                    "senior": (150000, 220000),
                    "principal": (200000, 300000)
                },
                "experience_benchmarks": {
                    "junior": {"min_years": 0, "max_years": 3, "typical_years": 2},
                    "mid": {"min_years": 3, "max_years": 7, "typical_years": 5},
                    "senior": {"min_years": 7, "max_years": 12, "typical_years": 9},
                    "principal": {"min_years": 10, "max_years": 18, "typical_years": 13}
                },
                "trending_skills": ["figma", "design systems", "accessibility", "ai-assisted design"],
                "declining_skills": ["photoshop for web", "flash", "outdated tools"],
                "hot_skills": ["user research", "prototyping", "design systems", "accessibility"],
                "saturated_skills": ["basic photoshop", "basic illustrator"],
                "high_demand_locations": ["San Francisco", "New York", "Los Angeles", "Austin"],
                "skill_premiums": {
                    "design systems": 1.2,
                    "user research": 1.15,
                    "accessibility": 1.1,
                    "motion design": 1.1
                }
            },
            
            "marketing": {
                "demand_level": 0.75,
                "market_saturation": 0.80,
                "growth_rate": 0.08,
                "competitiveness_score": 0.82,
                "salary_ranges": {
                    "junior": (40000, 70000),
                    "mid": (70000, 120000),
                    "senior": (120000, 180000),
                    "director": (180000, 250000)
                },
                "experience_benchmarks": {
                    "junior": {"min_years": 0, "max_years": 2, "typical_years": 1},
                    "mid": {"min_years": 2, "max_years": 5, "typical_years": 3.5},
                    "senior": {"min_years": 5, "max_years": 10, "typical_years": 7},
                    "director": {"min_years": 8, "max_years": 15, "typical_years": 11}
                },
                "trending_skills": ["growth marketing", "performance marketing", "ai marketing tools"],
                "declining_skills": ["traditional advertising", "print marketing"],
                "hot_skills": ["digital marketing", "analytics", "seo", "content marketing"],
                "saturated_skills": ["social media posting", "basic content creation"],
                "high_demand_locations": ["Major metropolitan areas"],
                "skill_premiums": {
                    "growth marketing": 1.2,
                    "performance marketing": 1.15,
                    "marketing automation": 1.1,
                    "data analysis": 1.15
                }
            }
        }
    
    def _load_enhanced_skill_market_data(self) -> Dict[str, Dict[str, float]]:
        """Load skill-specific market demand data."""
        return {
            # Programming Languages
            "python": {"demand": 0.95, "market_value": 90, "growth": 0.20},
            "javascript": {"demand": 0.90, "market_value": 85, "growth": 0.15},
            "typescript": {"demand": 0.85, "market_value": 88, "growth": 0.25},
            "java": {"demand": 0.80, "market_value": 80, "growth": 0.08},
            "go": {"demand": 0.85, "market_value": 92, "growth": 0.30},
            "rust": {"demand": 0.75, "market_value": 95, "growth": 0.40},
            "php": {"demand": 0.60, "market_value": 65, "growth": -0.05},
            
            # Frontend Technologies
            "react": {"demand": 0.90, "market_value": 88, "growth": 0.20},
            "vue": {"demand": 0.70, "market_value": 82, "growth": 0.15},
            "angular": {"demand": 0.75, "market_value": 80, "growth": 0.10},
            "html": {"demand": 0.40, "market_value": 40, "growth": 0.00},
            "css": {"demand": 0.45, "market_value": 45, "growth": 0.02},
            
            # Backend & Infrastructure
            "node.js": {"demand": 0.85, "market_value": 85, "growth": 0.18},
            "django": {"demand": 0.70, "market_value": 78, "growth": 0.12},
            "flask": {"demand": 0.65, "market_value": 75, "growth": 0.10},
            "docker": {"demand": 0.88, "market_value": 87, "growth": 0.22},
            "kubernetes": {"demand": 0.85, "market_value": 92, "growth": 0.28},
            "aws": {"demand": 0.92, "market_value": 90, "growth": 0.25},
            "gcp": {"demand": 0.80, "market_value": 88, "growth": 0.30},
            "azure": {"demand": 0.82, "market_value": 85, "growth": 0.20},
            
            # Data & AI
            "machine learning": {"demand": 0.90, "market_value": 95, "growth": 0.35},
            "deep learning": {"demand": 0.85, "market_value": 98, "growth": 0.40},
            "pytorch": {"demand": 0.80, "market_value": 92, "growth": 0.30},
            "tensorflow": {"demand": 0.75, "market_value": 88, "growth": 0.20},
            "sql": {"demand": 0.85, "market_value": 75, "growth": 0.10},
            "nosql": {"demand": 0.70, "market_value": 80, "growth": 0.15},
            "spark": {"demand": 0.75, "market_value": 85, "growth": 0.18},
            
            # Product & Design
            "figma": {"demand": 0.85, "market_value": 80, "growth": 0.25},
            "sketch": {"demand": 0.60, "market_value": 70, "growth": 0.05},
            "user research": {"demand": 0.80, "market_value": 85, "growth": 0.20},
            "prototyping": {"demand": 0.75, "market_value": 80, "growth": 0.15},
            "design systems": {"demand": 0.78, "market_value": 88, "growth": 0.22},
            
            # Soft Skills (lower market value but important)
            "communication": {"demand": 0.95, "market_value": 60, "growth": 0.05},
            "leadership": {"demand": 0.85, "market_value": 70, "growth": 0.08},
            "project management": {"demand": 0.80, "market_value": 65, "growth": 0.10},
            "agile": {"demand": 0.70, "market_value": 55, "growth": 0.05},
            "scrum": {"demand": 0.65, "market_value": 55, "growth": 0.05},
        }
    
    async def get_market_context(self, role_type: str, location: str = "general") -> MarketContext:
        """Generate market context for the given role and location."""
        
        # Get market data for the role
        role_data = self.market_data.get(role_type, self.market_data["general"])
        
        # Determine experience level (this would be calculated from resume in real implementation)
        experience_level = "mid"  # Default, should be determined from resume analysis
        
        # Get skill demand data for this role
        skill_demand = self._get_skill_demand_for_role(role_type)
        
        # Get salary range for experience level
        salary_ranges = role_data["salary_ranges"]
        salary_range = salary_ranges.get(experience_level, salary_ranges["mid"])
        
        # Get years experience benchmark
        experience_benchmarks = role_data["experience_benchmarks"]
        years_benchmark = {
            level: data["min_years"] + (data["max_years"] - data["min_years"]) // 2
            for level, data in experience_benchmarks.items()
        }
        
        return MarketContext(
            role_type=role_type,
            location=location,
            experience_level=experience_level,
            skill_demand=skill_demand,
            salary_range=salary_range,
            market_saturation=role_data["market_saturation"],
            years_experience_benchmark=years_benchmark
        )
    
    def _get_skill_demand_for_role(self, role_type: str) -> Dict[str, float]:
        """Get skill demand data specific to the role type."""
        
        # Map role types to relevant skills
        role_skill_mapping = {
            "software_engineer": [
                "python", "javascript", "typescript", "react", "node.js", 
                "docker", "kubernetes", "aws", "sql", "git"
            ],
            "data_scientist": [
                "python", "machine learning", "deep learning", "pytorch", 
                "tensorflow", "sql", "spark", "statistics"
            ],
            "product_manager": [
                "user research", "data analysis", "sql", "project management",
                "agile", "scrum", "roadmapping", "a/b testing"
            ],
            "designer": [
                "figma", "sketch", "user research", "prototyping", 
                "design systems", "accessibility", "user testing"
            ],
            "general": [
                "communication", "leadership", "project management", 
                "microsoft office", "problem solving"
            ]
        }
        
        # Get relevant skills for this role
        relevant_skills = role_skill_mapping.get(role_type, role_skill_mapping["general"])
        
        # Return demand scores for relevant skills
        skill_demand = {}
        for skill in relevant_skills:
            skill_data = self.skill_market_data.get(skill.lower(), {"demand": 0.5})
            skill_demand[skill.lower()] = skill_data["demand"]
        
        return skill_demand
    
    def get_market_data(self, role_type: str) -> Dict[str, Any]:
        """Get complete market data for a role type."""
        return self.market_data.get(role_type, self.market_data["general"])
    
    def get_skill_market_value(self, skill: str) -> Dict[str, float]:
        """Get market value data for a specific skill."""
        return self.skill_market_data.get(skill.lower(), {
            "demand": 0.5,
            "market_value": 50,
            "growth": 0.05
        })
    
    def calculate_realistic_score_adjustment(self, raw_score: float, role_type: str, 
                                           candidate_skills: List[str]) -> float:
        """Calculate realistic score adjustments based on market data."""
        
        role_data = self.get_market_data(role_type)
        adjustment = 0
        
        # Market saturation penalty
        saturation_penalty = role_data["market_saturation"] * 10
        adjustment -= saturation_penalty
        
        # High-demand skills bonus
        hot_skills = [skill.lower() for skill in role_data.get("hot_skills", [])]
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        
        matching_hot_skills = set(hot_skills) & set(candidate_skills_lower)
        hot_skills_bonus = len(matching_hot_skills) * 3
        adjustment += hot_skills_bonus
        
        # Saturated skills penalty
        saturated_skills = [skill.lower() for skill in role_data.get("saturated_skills", [])]
        matching_saturated_skills = set(saturated_skills) & set(candidate_skills_lower)
        saturated_penalty = len(matching_saturated_skills) * 2
        adjustment -= saturated_penalty
        
        # Apply adjustment while keeping score in realistic range
        adjusted_score = raw_score + adjustment
        return max(20, min(95, adjusted_score))
    
    def get_scoring_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get the realistic scoring distribution parameters."""
        return {
            "exceptional": {
                "percentage": 0.05,  # Top 5%
                "range": (85, 95),
                "description": "Outstanding candidates, top tier"
            },
            "strong": {
                "percentage": 0.20,  # Next 20%
                "range": (70, 84),
                "description": "Strong candidates, above average"
            },
            "good": {
                "percentage": 0.30,  # Next 30%
                "range": (55, 69),
                "description": "Good candidates, solid performers"
            },
            "average": {
                "percentage": 0.35,  # Next 35%
                "range": (40, 54),
                "description": "Average candidates, meet basic requirements"
            },
            "below_average": {
                "percentage": 0.10,  # Bottom 10%
                "range": (20, 39),
                "description": "Below average, significant gaps"
            }
        }
    
    def get_market_adjustments(self) -> Dict[str, float]:
        """Get market adjustment factors."""
        return {
            "high_saturation": -8,  # Penalty for high market saturation
            "low_saturation": 3,    # Bonus for low market saturation
            "high_demand_skill": 5, # Bonus per high-demand skill
            "rare_skill": 8,        # Bonus for rare/valuable skills
            "saturated_skill": -3,  # Penalty per oversaturated skill
            "location_premium": 5,  # Bonus for high-demand locations
            "experience_mismatch": -10  # Penalty for experience level mismatch
        }
    
    def get_experience_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """Get experience level benchmarks across roles."""
        return {
            "title_progression_patterns": {
                "software": ["Junior Developer", "Developer", "Senior Developer", "Lead Developer", "Principal Engineer"],
                "product": ["Associate PM", "Product Manager", "Senior PM", "Principal PM", "Director of Product"],
                "data": ["Data Analyst", "Data Scientist", "Senior Data Scientist", "Principal Data Scientist", "Head of Data"],
                "design": ["Junior Designer", "Designer", "Senior Designer", "Lead Designer", "Design Director"]
            },
            "responsibility_benchmarks": {
                "junior": ["Individual contributor", "Learning and growth focused", "Guided by senior team members"],
                "mid": ["Independent contributor", "Project ownership", "Mentoring junior members"],
                "senior": ["Technical leadership", "Architecture decisions", "Cross-team collaboration"],
                "principal": ["Strategic leadership", "Company-wide impact", "Defining technical direction"]
            },
            "years_experience_ranges": {
                "junior": {"min": 0, "typical": 1, "max": 2},
                "mid": {"min": 2, "typical": 4, "max": 6},
                "senior": {"min": 5, "typical": 8, "max": 12},
                "principal": {"min": 8, "typical": 12, "max": 20}
            }
        }
