
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from analysis.backtesting import get_available_strategies, run_backtest
from utils.logging_config import get_logger

logger = get_logger(__name__)

class PortfolioOptimizer:
    def __init__(self):
        self.strategies = get_available_strategies()
        
    def optimize_portfolio_allocation(self, symbols, days=365, initial_capital=10000):
        """Optimize portfolio allocation across multiple symbols and strategies"""
        try:
            # Run backtests for all symbol-strategy combinations
            backtest_results = {}
            
            for symbol in symbols:
                backtest_results[symbol] = {}
                for strategy in self.strategies:
                    result = run_backtest(symbol, strategy, days=days, initial_capital=initial_capital)
                    if result:
                        backtest_results[symbol][strategy.name] = result['metrics']
            
            # Find optimal allocation using mean-variance optimization
            best_allocation = self._mean_variance_optimization(backtest_results)
            
            return best_allocation
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {str(e)}", exc_info=True)
            return None
    
    def _mean_variance_optimization(self, results):
        """Perform mean-variance optimization"""
        # Extract returns and risks
        returns = []
        risks = []
        combinations = []
        
        for symbol, strategies in results.items():
            for strategy_name, metrics in strategies.items():
                if metrics['annual_return_pct'] is not None:
                    returns.append(metrics['annual_return_pct'])
                    risks.append(metrics['annual_volatility_pct'])
                    combinations.append((symbol, strategy_name))
        
        if not returns:
            return None
            
        returns = np.array(returns)
        risks = np.array(risks)
        
        # Objective: maximize Sharpe ratio
        def objective(weights):
            portfolio_return = np.dot(weights, returns)
            portfolio_risk = np.sqrt(np.dot(weights**2, risks**2))
            if portfolio_risk == 0:
                return -float('inf')
            return -(portfolio_return / portfolio_risk)  # Negative for minimization
        
        # Constraints
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in returns)
        
        # Initial guess
        n_assets = len(returns)
        x0 = np.array([1/n_assets] * n_assets)
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            optimal_weights = result.x
            allocation = {}
            for i, (symbol, strategy) in enumerate(combinations):
                if optimal_weights[i] > 0.01:  # Only include significant allocations
                    allocation[f"{symbol}_{strategy}"] = {
                        'weight': optimal_weights[i],
                        'symbol': symbol,
                        'strategy': strategy,
                        'expected_return': returns[i],
                        'risk': risks[i]
                    }
            return allocation
        
        return None
    
    def create_mega_strategy(self, top_performers):
        """Create a mega-strategy combining the best performers"""
        mega_signals = {}
        
        for symbol_strategy, data in top_performers.items():
            weight = data['weight']
            symbol = data['symbol']
            
            # Weight signals by performance
            if symbol not in mega_signals:
                mega_signals[symbol] = 0
            
            # Add weighted signal strength
            mega_signals[symbol] += weight * data['expected_return']
        
        return mega_signals
