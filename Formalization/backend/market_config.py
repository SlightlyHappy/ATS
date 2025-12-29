"""
Market Context and Realistic Scoring Configuration
This module contains market data, benchmarks, and scoring parameters for realistic resume analysis.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime

# =============================================================================
# MARKET DATA CONFIGURATION
# =============================================================================

MARKET_DATA = {
    "software_engineer": {
        "demand_level": 0.9,  # High demand
        "market_saturation": 0.7,  # Moderately saturated
        "growth_rate": 0.15,  # 15% annual growth
        "salary_ranges": {
            "junior": (70000, 120000),
            "mid": (120000, 180000),
            "senior": (180000, 300000),
            "principal": (250000, 450000)
        },
        "experience_benchmarks": {
            "junior": {"min_years": 0, "max_years": 2},
            "mid": {"min_years": 2, "max_years": 5},
            "senior": {"min_years": 5, "max_years": 10},
            "principal": {"min_years": 8, "max_years": 15}
        },
        "hot_skills": ["python", "react", "aws", "kubernetes", "machine learning"],
        "saturated_skills": ["html", "css", "basic javascript"],
        "high_demand_locations": ["San Francisco", "New York", "Seattle", "Austin", "Boston"]
    },
    
    "product_manager": {
        "demand_level": 0.8,
        "market_saturation": 0.8,  # High saturation
        "growth_rate": 0.12,
        "salary_ranges": {
            "junior": (80000, 130000),
            "mid": (130000, 200000),
            "senior": (200000, 350000),
            "director": (300000, 500000)
        },
        "experience_benchmarks": {
            "junior": {"min_years": 0, "max_years": 3},
            "mid": {"min_years": 3, "max_years": 7},
            "senior": {"min_years": 7, "max_years": 12},
            "director": {"min_years": 10, "max_years": 20}
        },
        "hot_skills": ["user research", "data analysis", "sql", "roadmapping", "a/b testing"],
        "saturated_skills": ["agile", "scrum", "communication"],
        "high_demand_locations": ["San Francisco", "New York", "Seattle", "Los Angeles"]
    },
    
    "data_scientist": {
        "demand_level": 0.85,
        "market_saturation": 0.6,  # Moderate saturation
        "growth_rate": 0.20,
        "salary_ranges": {
            "junior": (90000, 140000),
            "mid": (140000, 200000),
            "senior": (200000, 320000),
            "principal": (280000, 450000)
        },
        "experience_benchmarks": {
            "junior": {"min_years": 0, "max_years": 2},
            "mid": {"min_years": 2, "max_years": 5},
            "senior": {"min_years": 5, "max_years": 10},
            "principal": {"min_years": 8, "max_years": 15}
        },
        "hot_skills": ["machine learning", "deep learning", "pytorch", "tensorflow", "mlops"],
        "saturated_skills": ["excel", "basic python", "basic sql"],
        "high_demand_locations": ["San Francisco", "New York", "Boston", "Seattle", "Austin"]
    },
    
    "designer": {
        "demand_level": 0.7,
        "market_saturation": 0.75,
        "growth_rate": 0.10,
        "salary_ranges": {
            "junior": (60000, 100000),
            "mid": (100000, 150000),
            "senior": (150000, 220000),
            "principal": (200000, 300000)
        },
        "experience_benchmarks": {
            "junior": {"min_years": 0, "max_years": 3},
            "mid": {"min_years": 3, "max_years": 6},
            "senior": {"min_years": 6, "max_years": 12},
            "principal": {"min_years": 10, "max_years": 20}
        },
        "hot_skills": ["figma", "user research", "prototyping", "design systems", "accessibility"],
        "saturated_skills": ["photoshop", "illustrator", "basic design"],
        "high_demand_locations": ["San Francisco", "New York", "Los Angeles", "Seattle"]
    }
}

# =============================================================================
# SKILL MARKET VALUE DATABASE
# =============================================================================

SKILL_MARKET_VALUE = {
    # Programming Languages
    "python": {"demand": 0.95, "rarity": 0.3, "growth": 0.15, "market_value": 85},
    "javascript": {"demand": 0.90, "rarity": 0.2, "growth": 0.10, "market_value": 80},
    "typescript": {"demand": 0.85, "rarity": 0.4, "growth": 0.25, "market_value": 88},
    "java": {"demand": 0.80, "rarity": 0.3, "growth": 0.05, "market_value": 75},
    "go": {"demand": 0.75, "rarity": 0.7, "growth": 0.30, "market_value": 90},
    "rust": {"demand": 0.65, "rarity": 0.8, "growth": 0.40, "market_value": 92},
    
    # Frontend Technologies
    "react": {"demand": 0.90, "rarity": 0.3, "growth": 0.15, "market_value": 85},
    "vue.js": {"demand": 0.70, "rarity": 0.5, "growth": 0.20, "market_value": 82},
    "angular": {"demand": 0.75, "rarity": 0.4, "growth": 0.10, "market_value": 78},
    "svelte": {"demand": 0.60, "rarity": 0.8, "growth": 0.35, "market_value": 88},
    
    # Backend Technologies
    "node.js": {"demand": 0.85, "rarity": 0.3, "growth": 0.12, "market_value": 82},
    "django": {"demand": 0.70, "rarity": 0.4, "growth": 0.08, "market_value": 78},
    "flask": {"demand": 0.65, "rarity": 0.5, "growth": 0.10, "market_value": 75},
    "spring boot": {"demand": 0.75, "rarity": 0.4, "growth": 0.06, "market_value": 76},
    
    # Cloud Platforms
    "aws": {"demand": 0.95, "rarity": 0.4, "growth": 0.20, "market_value": 90},
    "azure": {"demand": 0.80, "rarity": 0.5, "growth": 0.18, "market_value": 85},
    "gcp": {"demand": 0.70, "rarity": 0.6, "growth": 0.22, "market_value": 87},
    "kubernetes": {"demand": 0.85, "rarity": 0.6, "growth": 0.25, "market_value": 92},
    "docker": {"demand": 0.88, "rarity": 0.4, "growth": 0.15, "market_value": 85},
    
    # Data & AI
    "machine learning": {"demand": 0.95, "rarity": 0.7, "growth": 0.30, "market_value": 95},
    "deep learning": {"demand": 0.85, "rarity": 0.8, "growth": 0.35, "market_value": 98},
    "pytorch": {"demand": 0.80, "rarity": 0.7, "growth": 0.28, "market_value": 92},
    "tensorflow": {"demand": 0.78, "rarity": 0.6, "growth": 0.20, "market_value": 88},
    "mlops": {"demand": 0.90, "rarity": 0.9, "growth": 0.45, "market_value": 98},
    
    # Databases
    "postgresql": {"demand": 0.85, "rarity": 0.4, "growth": 0.12, "market_value": 82},
    "mongodb": {"demand": 0.75, "rarity": 0.5, "growth": 0.15, "market_value": 80},
    "redis": {"demand": 0.70, "rarity": 0.6, "growth": 0.18, "market_value": 85},
    
    # Blockchain & Emerging
    "blockchain": {"demand": 0.60, "rarity": 0.85, "growth": 0.25, "market_value": 90},
    "solidity": {"demand": 0.50, "rarity": 0.9, "growth": 0.30, "market_value": 95},
    "web3": {"demand": 0.55, "rarity": 0.8, "growth": 0.40, "market_value": 92},
}

# =============================================================================
# REALISTIC SCORING FRAMEWORK CONFIGURATION
# =============================================================================

SCORING_DISTRIBUTION = {
    "exceptional": {
        "range": (85, 100),
        "target_percentage": 5,  # Only top 5% should be exceptional
        "description": "Outstanding candidates who exceed expectations"
    },
    "strong": {
        "range": (70, 84),
        "target_percentage": 15,  # Next 15% are strong candidates
        "description": "Strong candidates who meet most requirements well"
    },
    "good": {
        "range": (55, 69),
        "target_percentage": 30,  # 30% are good, solid candidates
        "description": "Good candidates who meet basic requirements"
    },
    "average": {
        "range": (40, 54),
        "target_percentage": 35,  # 35% are average
        "description": "Average candidates with some qualifications"
    },
    "below_average": {
        "range": (20, 39),
        "target_percentage": 15,  # Bottom 15%
        "description": "Below average candidates with significant gaps"
    }
}

# Market competitiveness adjustments
MARKET_ADJUSTMENTS = {
    "high_saturation": -8,      # Saturated markets are more competitive
    "medium_saturation": -4,    # Moderate competition
    "low_saturation": +2,       # Less competitive markets
    
    "high_demand_skill": +5,    # Rare, in-demand skills get bonus
    "emerging_skill": +3,       # New technologies get small bonus
    "deprecated_skill": -5,     # Outdated skills get penalty
    
    "tier1_company": +10,       # FAANG/Tier 1 companies
    "tier2_company": +5,        # Well-known companies
    "startup": +2,              # Startup experience
    "unknown_company": -2,      # Unknown companies
}

# Experience validation benchmarks
EXPERIENCE_BENCHMARKS = {
    "title_progression_patterns": {
        "software_engineer": [
            "intern", "junior", "software engineer", "senior software engineer", 
            "staff engineer", "principal engineer", "distinguished engineer"
        ],
        "product_manager": [
            "associate pm", "product manager", "senior product manager",
            "principal product manager", "director of product", "vp product"
        ],
        "data_scientist": [
            "data analyst", "junior data scientist", "data scientist",
            "senior data scientist", "principal data scientist", "staff data scientist"
        ]
    },
    
    "responsibility_evolution": {
        "junior": ["learn", "implement", "support", "assist"],
        "mid": ["design", "lead", "mentor", "coordinate"],
        "senior": ["architect", "strategy", "manage", "influence"],
        "principal": ["vision", "cross-org", "technical leadership", "industry impact"]
    },
    
    "red_flags": {
        "unrealistic_progression": "Promotion from junior to senior in < 2 years",
        "responsibility_mismatch": "Senior responsibilities claimed with junior years",
        "skill_experience_gap": "Claimed expertise without supporting experience",
        "frequent_job_changes": "More than 4 jobs in 3 years without explanation",
        "employment_gaps": "Unexplained gaps > 6 months",
        "inflated_titles": "Inflated job titles compared to company size/type"
    }
}

# =============================================================================
# ROLE-SPECIFIC REQUIREMENTS TEMPLATES
# =============================================================================

ROLE_REQUIREMENTS_TEMPLATES = {
    "software_engineer": {
        "must_have": {
            "technical_skills": ["programming languages", "version control", "debugging"],
            "experience": ["software development", "code review", "testing"],
            "soft_skills": ["problem solving", "collaboration"]
        },
        "nice_to_have": {
            "technical_skills": ["cloud platforms", "devops", "system design"],
            "experience": ["agile development", "mentoring", "open source"],
            "soft_skills": ["leadership", "communication"]
        },
        "deal_breakers": ["no programming experience", "cannot code"]
    },
    
    "product_manager": {
        "must_have": {
            "skills": ["product strategy", "user research", "data analysis"],
            "experience": ["product development", "stakeholder management"],
            "soft_skills": ["communication", "decision making"]
        },
        "nice_to_have": {
            "skills": ["technical background", "design thinking", "sql"],
            "experience": ["startup experience", "B2B/B2C products"],
            "soft_skills": ["leadership", "negotiation"]
        },
        "deal_breakers": ["no product experience", "no user focus"]
    }
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_market_data(role_type: str) -> Dict[str, Any]:
    """Get market data for a specific role type."""
    # Normalize role type
    role_key = normalize_role_type(role_type)
    return MARKET_DATA.get(role_key, get_default_market_data())

def normalize_role_type(role_type: str) -> str:
    """Normalize role type to match our market data keys."""
    role_lower = role_type.lower()
    
    if any(term in role_lower for term in ['software', 'developer', 'engineer', 'programmer']):
        return "software_engineer"
    elif any(term in role_lower for term in ['product', 'pm']) and 'manager' in role_lower:
        return "product_manager"
    elif any(term in role_lower for term in ['data scientist', 'ml engineer', 'ai']):
        return "data_scientist"
    elif any(term in role_lower for term in ['designer', 'ux', 'ui']):
        return "designer"
    else:
        return "general"

def get_default_market_data() -> Dict[str, Any]:
    """Get default market data for unknown roles."""
    return {
        "demand_level": 0.6,
        "market_saturation": 0.6,
        "growth_rate": 0.08,
        "salary_ranges": {
            "junior": (50000, 80000),
            "mid": (80000, 120000),
            "senior": (120000, 200000)
        },
        "experience_benchmarks": {
            "junior": {"min_years": 0, "max_years": 2},
            "mid": {"min_years": 2, "max_years": 5},
            "senior": {"min_years": 5, "max_years": 10}
        },
        "hot_skills": [],
        "saturated_skills": [],
        "high_demand_locations": ["Major Cities"]
    }

def get_skill_market_value(skill: str) -> Dict[str, float]:
    """Get market value data for a specific skill."""
    skill_lower = skill.lower()
    
    # Direct match
    if skill_lower in SKILL_MARKET_VALUE:
        return SKILL_MARKET_VALUE[skill_lower]
    
    # Partial match for similar skills
    for market_skill, data in SKILL_MARKET_VALUE.items():
        if skill_lower in market_skill or market_skill in skill_lower:
            return data
    
    # Default values for unknown skills
    return {
        "demand": 0.5,
        "rarity": 0.5,
        "growth": 0.0,
        "market_value": 50
    }

def calculate_realistic_score_adjustment(base_score: float, role_type: str, 
                                       skills: List[str], experience_years: float) -> float:
    """Calculate realistic score adjustment based on market conditions."""
    
    market_data = get_market_data(role_type)
    adjustment = 0
    
    # Market saturation penalty
    saturation = market_data.get("market_saturation", 0.6)
    adjustment -= saturation * 10
    
    # Skill market value bonus/penalty
    skill_bonus = 0
    for skill in skills:
        skill_data = get_skill_market_value(skill)
        if skill_data["market_value"] > 85:
            skill_bonus += 2
        elif skill_data["market_value"] < 60:
            skill_bonus -= 1
    
    adjustment += min(skill_bonus, 10)  # Cap skill bonus
    
    # Experience appropriateness
    exp_benchmarks = market_data.get("experience_benchmarks", {})
    if experience_years < 2:
        level = "junior"
    elif experience_years < 5:
        level = "mid"
    else:
        level = "senior"
    
    expected_range = exp_benchmarks.get(level, {"min_years": 0, "max_years": 10})
    if not (expected_range["min_years"] <= experience_years <= expected_range["max_years"]):
        adjustment -= 5  # Experience mismatch penalty
    
    # Apply adjustment with bounds
    adjusted_score = base_score + adjustment
    return max(20, min(95, adjusted_score))  # Keep within realistic bounds

def get_scoring_distribution() -> Dict[str, Any]:
    """Get the scoring distribution configuration."""
    return SCORING_DISTRIBUTION.copy()

def get_all_skill_market_values() -> Dict[str, Dict[str, float]]:
    """Get all skill market value data."""
    return SKILL_MARKET_VALUE.copy()
