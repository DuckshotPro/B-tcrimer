
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
import pandas as pd
import numpy as np
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AdvancedRiskManager:
    def __init__(self):
        self.max_position_size = 0.25  # Maximum 25% of capital per position
        self.max_portfolio_risk = 0.15  # Maximum 15% portfolio risk
        self.stop_loss_threshold = 0.05  # 5% stop loss
        
    def calculate_position_size(self, capital, confidence, risk_level, expected_return):
        """Calculate optimal position size based on risk parameters"""
        try:
            # Base position size using Kelly Criterion approximation
            win_prob = confidence
            avg_win = abs(expected_return) if expected_return > 0 else 5.0
            avg_loss = avg_win * 0.5  # Assume 2:1 reward/risk ratio
            
            # Kelly fraction
            kelly_fraction = (win_prob * avg_win - (1 - win_prob) * avg_loss) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            
            # Risk level adjustment
            risk_multipliers = {
                'LOW': 1.2,
                'MEDIUM': 1.0,
                'HIGH': 0.7
            }
            
            risk_multiplier = risk_multipliers.get(risk_level, 1.0)
            
            # Final position size
            position_size = capital * kelly_fraction * risk_multiplier
            
            # Apply maximum position limit
            max_position = capital * self.max_position_size
            position_size = min(position_size, max_position)
            
            return position_size
            
        except Exception as e:
            logger.error(f"Position size calculation failed: {str(e)}", exc_info=True)
            return capital * 0.1  # Default to 10%
    
    def assess_portfolio_risk(self, positions):
        """Assess overall portfolio risk"""
        try:
            if not positions:
                return {'risk_level': 'LOW', 'risk_score': 0}
            
            total_exposure = sum(pos['position_size'] for pos in positions)
            position_count = len(positions)
            
            # Calculate risk score
            risk_score = 0
            
            # Concentration risk
            if position_count == 1:
                risk_score += 0.3
            elif position_count <= 3:
                risk_score += 0.2
            elif position_count <= 5:
                risk_score += 0.1
            
            # Exposure risk
            if total_exposure > 0.8:  # More than 80% deployed
                risk_score += 0.3
            elif total_exposure > 0.6:
                risk_score += 0.2
            elif total_exposure > 0.4:
                risk_score += 0.1
            
            # Individual position risk
            high_risk_positions = sum(1 for pos in positions if pos.get('risk_level') == 'HIGH')
            risk_score += (high_risk_positions / position_count) * 0.2
            
            # Determine risk level
            if risk_score >= 0.6:
                risk_level = 'HIGH'
            elif risk_score >= 0.3:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'total_exposure': total_exposure,
                'position_count': position_count
            }
            
        except Exception as e:
            logger.error(f"Portfolio risk assessment failed: {str(e)}", exc_info=True)
            return {'risk_level': 'HIGH', 'risk_score': 1.0}
    
    def should_stop_trading(self, current_capital, initial_capital, consecutive_losses=0):
        """Determine if trading should be stopped"""
        # Stop if capital drops below 50% of initial
        if current_capital < initial_capital * 0.5:
            return True, "Capital dropped below 50% of initial amount"
        
        # Stop after 5 consecutive losses
        if consecutive_losses >= 5:
            return True, "Too many consecutive losses"
        
        # Stop if capital is too low for meaningful trading
        if current_capital < 25:
            return True, "Insufficient capital for trading"
        
        return False, None
