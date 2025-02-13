from typing import Dict, Any, Optional
import math

class ProjectionsService:
    """Service for calculating account value projections"""
    
    def __init__(self):
        pass

    def get_account_projection(self, account_value: float, years: int, growth_rate: Optional[float] = 0.07) -> Dict[str, Any]:
        """
        Calculate the projected account value based on initial value, time period and growth rate
        
        Args:
            account_value (float): Initial account value
            years (int): Number of years to project
            growth_rate (float, optional): Annual growth rate as decimal. Defaults to 0.07 (7%)
            
        Returns:
            Dict[str, Any]: Dictionary containing projected value and input parameters
        """
        # Calculate future value using compound interest formula
        # FV = PV * (1 + r)^t
        projected_value = account_value * ((1 + growth_rate) ** years)
        
        return {
            "projected_value": round(projected_value, 2),
            "initial_value": account_value,
            "years": years,
            "growth_rate": growth_rate,
            "growth_rate_percentage": f"{growth_rate * 100}%"
        }