from b_tcrimer.analysis.backtesting import run_backtest as original_run_backtest, get_available_strategies
from b_tcrimer.analysis.backtesting import MovingAverageCrossoverStrategy, RSIStrategy, MACDStrategy

def run_backtest(strategy_name: str, symbol: str, start_date: str, end_date: str):
    # Map strategy name to strategy object
    strategy_map = {
        "MovingAverageCrossoverStrategy": MovingAverageCrossoverStrategy(20, 50), # Default periods
        "RSIStrategy": RSIStrategy(14, 70, 30), # Default periods
        "MACDStrategy": MACDStrategy(12, 26, 9) # Default periods
    }

    strategy = strategy_map.get(strategy_name)
    if not strategy:
        return {"error": f"Strategy '{strategy_name}' not found."}

    # Convert start_date and end_date to days for the original run_backtest function
    # This is a simplification; a more robust solution would handle date parsing
    # and pass actual datetime objects if the original function supported it.
    # For now, we'll calculate days based on a fixed end date (today) and start date.
    from datetime import datetime
    end_datetime = datetime.now()
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    days = (end_datetime - start_datetime).days

    # Call the original run_backtest function
    backtest_results = original_run_backtest(
        symbol=symbol,
        strategy=strategy,
        days=days, # Pass calculated days
        # Add other parameters as needed, or use defaults
        # exchange='binance',
        # initial_capital=10000.0,
        # position_size=0.1,
        # stop_loss=0.05
    )

    if backtest_results and "metrics" in backtest_results:
        metrics = backtest_results["metrics"]
        return {
            "strategy": strategy_name,
            "symbol": symbol,
            "total_return_pct": metrics.get("total_return_pct", 0.0),
            "max_drawdown_pct": metrics.get("max_drawdown_pct", 0.0),
            "sharpe_ratio": metrics.get("sharpe_ratio", 0.0),
            "profit": metrics.get("final_capital", 0.0) - metrics.get("initial_capital", 0.0)
        }
    else:
        return {"strategy": strategy_name, "symbol": symbol, "profit": 0.0, "drawdown": 0.0}