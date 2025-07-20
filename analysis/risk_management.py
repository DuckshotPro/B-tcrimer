
import pandas as pd
import numpy as np
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AdvancedRiskManager:
    def __init__(self, max_portfolio_risk=0.02, max_single_position=0.1):
        self.max_portfolio_risk = max_portfolio_risk  # 2% max daily loss
        self.max_single_position = max_single_position  # 10% max per position
        
    def calculate_position_size(self, account_balance, entry_price, stop_loss_price, confidence_score=0.5):
        """Calculate optimal position size using Kelly Criterion with risk limits"""
        try:
            # Kelly Criterion: f = (bp - q) / b
            # Where: f = fraction of capital, b = odds, p = probability of win, q = probability of loss
            
            risk_per_share = abs(entry_price - stop_loss_price)
            risk_reward_ratio = risk_per_share / entry_price
            
            # Adjust Kelly fraction by confidence score
            kelly_fraction = confidence_score * 0.25  # Conservative Kelly
            
            # Apply risk limits
            max_risk_amount = account_balance * self.max_portfolio_risk
            max_position_amount = account_balance * self.max_single_position
            
            # Position size based on risk
            position_size_by_risk = max_risk_amount / risk_per_share
            position_value_by_risk = position_size_by_risk * entry_price
            
            # Position size based on Kelly
            kelly_position_value = account_balance * kelly_fraction
            
            # Take the minimum to be conservative
            final_position_value = min(position_value_by_risk, kelly_position_value, max_position_amount)
            final_position_size = final_position_value / entry_price
            
            return {
                'position_size': final_position_size,
                'position_value': final_position_value,
                'risk_amount': final_position_size * risk_per_share,
                'risk_percentage': (final_position_size * risk_per_share) / account_balance * 100
            }
        except Exception as e:
            logger.error(f"Position size calculation failed: {str(e)}", exc_info=True)
            return {'position_size': 0, 'position_value': 0, 'risk_amount': 0, 'risk_percentage': 0}
    
    def dynamic_stop_loss(self, entry_price, current_price, atr, profit_factor=2):
        """Calculate dynamic trailing stop loss"""
        try:
            # Initial stop loss at 2x ATR
            initial_stop = entry_price - (2 * atr)
            
            # If in profit, trail the stop
            if current_price > entry_price:
                profit = current_price - entry_price
                trailing_stop = current_price - (profit / profit_factor)  # Trail at 50% of profit
                return max(initial_stop, trailing_stop)
            
            return initial_stop
        except Exception as e:
            logger.error(f"Dynamic stop loss calculation failed: {str(e)}", exc_info=True)
            return entry_price * 0.95  # 5% emergency stop
    
    def portfolio_heat(self, positions):
        """Calculate total portfolio risk exposure"""
        total_risk = sum(pos.get('risk_percentage', 0) for pos in positions)
        return min(total_risk, 100)  # Cap at 100%
