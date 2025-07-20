
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analysis.signal_generator import AutomatedSignalGenerator
from analysis.portfolio_optimizer import PortfolioOptimizer
from analysis.risk_management import AdvancedRiskManager
from utils.logging_config import get_logger
from database.operations import get_db_connection
import time

logger = get_logger(__name__)

class DominoCascadeSystem:
    def __init__(self, initial_capital=100.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.signal_generator = AutomatedSignalGenerator()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.risk_manager = AdvancedRiskManager()
        self.cascade_history = []
        self.reinvestment_rate = 0.8  # Reinvest 80% of profits
        self.min_trade_size = 10.0    # Minimum $10 per trade
        
    def execute_cascade_cycle(self):
        """Execute one complete domino cascade cycle"""
        try:
            logger.info(f"Starting cascade cycle with ${self.current_capital:.2f}")
            
            # Step 1: Get top opportunities
            opportunities = self.signal_generator.get_top_opportunities(limit=5)
            
            if not opportunities:
                logger.warning("No trading opportunities found")
                return False
            
            # Step 2: Calculate position sizes for each opportunity
            positions = self._calculate_cascade_positions(opportunities)
            
            # Step 3: Simulate trades and calculate returns
            cycle_results = self._simulate_cascade_trades(positions)
            
            # Step 4: Update capital and record results
            self._update_capital_cascade(cycle_results)
            
            # Step 5: Log cycle completion
            self._log_cascade_cycle(cycle_results)
            
            return True
            
        except Exception as e:
            logger.error(f"Cascade cycle failed: {str(e)}", exc_info=True)
            return False
    
    def _calculate_cascade_positions(self, opportunities):
        """Calculate position sizes using cascade strategy"""
        positions = []
        available_capital = self.current_capital
        
        # Allocate capital in descending order of confidence
        for i, opp in enumerate(opportunities):
            if available_capital < self.min_trade_size:
                break
                
            # Progressive allocation: First gets most, subsequent get less
            allocation_factor = 1.0 / (i + 1)  # 100%, 50%, 33%, 25%, 20%
            base_allocation = available_capital * 0.3 * allocation_factor
            
            # Risk-adjusted position size
            risk_multiplier = self._get_risk_multiplier(opp['confidence'], opp['risk_level'])
            position_size = min(base_allocation * risk_multiplier, available_capital * 0.5)
            
            if position_size >= self.min_trade_size:
                positions.append({
                    'symbol': opp['symbol'],
                    'signal': opp['signal'],
                    'position_size': position_size,
                    'confidence': opp['confidence'],
                    'expected_return': opp['expected_return'],
                    'risk_level': opp['risk_level']
                })
                available_capital -= position_size
        
        return positions
    
    def _get_risk_multiplier(self, confidence, risk_level):
        """Calculate risk multiplier based on confidence and risk level"""
        confidence_multiplier = confidence  # 0.6-1.0
        
        risk_multipliers = {
            'LOW': 1.2,
            'MEDIUM': 1.0,
            'HIGH': 0.8
        }
        
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        return confidence_multiplier * risk_multiplier
    
    def _simulate_cascade_trades(self, positions):
        """Simulate the cascade trades and calculate returns"""
        results = []
        
        for position in positions:
            # Simulate market execution with some randomness
            base_return = position['expected_return'] / 100  # Convert to decimal
            
            # Add market noise (±20% variance)
            market_noise = np.random.normal(0, 0.2)
            actual_return = base_return * (1 + market_noise)
            
            # Apply confidence factor to success probability
            success_probability = position['confidence']
            trade_success = np.random.random() < success_probability
            
            if not trade_success:
                actual_return = -abs(actual_return) * 0.5  # Loss scenario
            
            # Calculate profit/loss
            pnl = position['position_size'] * actual_return
            
            results.append({
                'symbol': position['symbol'],
                'position_size': position['position_size'],
                'return_pct': actual_return * 100,
                'pnl': pnl,
                'success': trade_success,
                'timestamp': datetime.now()
            })
        
        return results
    
    def _update_capital_cascade(self, cycle_results):
        """Update capital based on cascade results"""
        total_pnl = sum(result['pnl'] for result in cycle_results)
        
        # Update current capital
        self.current_capital += total_pnl
        
        # Record this cycle
        cycle_summary = {
            'cycle_number': len(self.cascade_history) + 1,
            'starting_capital': self.current_capital - total_pnl,
            'ending_capital': self.current_capital,
            'total_pnl': total_pnl,
            'return_pct': (total_pnl / (self.current_capital - total_pnl)) * 100,
            'trades': cycle_results,
            'timestamp': datetime.now()
        }
        
        self.cascade_history.append(cycle_summary)
    
    def _log_cascade_cycle(self, cycle_results):
        """Log the cascade cycle results"""
        total_pnl = sum(result['pnl'] for result in cycle_results)
        cycle_num = len(self.cascade_history)
        
        logger.info(f"Cascade Cycle #{cycle_num} completed:")
        logger.info(f"  Capital: ${self.current_capital:.2f}")
        logger.info(f"  P&L: ${total_pnl:+.2f}")
        logger.info(f"  Trades: {len(cycle_results)}")
        
        for result in cycle_results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"  {status} {result['symbol']}: ${result['pnl']:+.2f} ({result['return_pct']:+.1f}%)")
    
    def run_automated_cascade(self, cycles=10, delay_minutes=60):
        """Run automated cascade for specified cycles"""
        logger.info(f"Starting automated domino cascade: {cycles} cycles, {delay_minutes}min intervals")
        
        for cycle in range(cycles):
            logger.info(f"Starting cycle {cycle + 1}/{cycles}")
            
            success = self.execute_cascade_cycle()
            
            if not success:
                logger.warning(f"Cycle {cycle + 1} failed, continuing...")
            
            # Check if we've reached million dollar target
            if self.current_capital >= 1000000:
                logger.info("🎉 MILLION DOLLAR TARGET REACHED! 🎉")
                break
            
            # Check if capital is too low to continue
            if self.current_capital < self.min_trade_size:
                logger.warning("Insufficient capital to continue cascade")
                break
            
            # Wait before next cycle (except for last cycle)
            if cycle < cycles - 1:
                time.sleep(delay_minutes * 60)
        
        return self.get_cascade_summary()
    
    def get_cascade_summary(self):
        """Get summary of cascade performance"""
        if not self.cascade_history:
            return None
        
        total_return = (self.current_capital / self.initial_capital - 1) * 100
        total_cycles = len(self.cascade_history)
        
        successful_cycles = sum(1 for cycle in self.cascade_history if cycle['total_pnl'] > 0)
        win_rate = successful_cycles / total_cycles * 100
        
        avg_return_per_cycle = total_return / total_cycles if total_cycles > 0 else 0
        
        # Calculate time to million
        if total_return > 0:
            cycles_to_million = np.log(1000000 / self.initial_capital) / np.log(1 + avg_return_per_cycle / 100)
        else:
            cycles_to_million = float('inf')
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_return_pct': total_return,
            'total_cycles': total_cycles,
            'win_rate': win_rate,
            'avg_return_per_cycle': avg_return_per_cycle,
            'estimated_cycles_to_million': cycles_to_million,
            'cascade_history': self.cascade_history
        }
    
    def save_cascade_to_db(self):
        """Save cascade results to database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create cascade table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS domino_cascade (
                    id SERIAL PRIMARY KEY,
                    cycle_number INTEGER,
                    starting_capital DECIMAL(15,2),
                    ending_capital DECIMAL(15,2),
                    total_pnl DECIMAL(15,2),
                    return_pct DECIMAL(8,4),
                    trades_data TEXT,
                    timestamp TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert cascade history
            for cycle in self.cascade_history:
                cursor.execute("""
                    INSERT INTO domino_cascade 
                    (cycle_number, starting_capital, ending_capital, total_pnl, return_pct, trades_data, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    cycle['cycle_number'],
                    cycle['starting_capital'],
                    cycle['ending_capital'],
                    cycle['total_pnl'],
                    cycle['return_pct'],
                    str(cycle['trades']),
                    cycle['timestamp']
                ))
            
            conn.commit()
            conn.close()
            
            logger.info("Cascade data saved to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cascade data: {str(e)}", exc_info=True)
            return False
