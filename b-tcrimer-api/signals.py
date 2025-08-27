from b_tcrimer.analysis.signal_generator import AutomatedSignalGenerator

def get_signals(symbol: str):
    signal_generator = AutomatedSignalGenerator()
    # generate_mega_signals expects a list of symbols
    mega_signals = signal_generator.generate_mega_signals(symbols=[symbol])

    if mega_signals:
        # Assuming we take the first signal if multiple are returned for a single symbol
        signal_data = mega_signals[0]
        return {
            "symbol": signal_data['symbol'],
            "signal_strength": signal_data['signal'],
            "entry_price": signal_data.get('entry_price', 0.0), # entry_price is not directly in signal_data, will need to be derived or added
            "exit_price": signal_data.get('exit_price', 0.0),   # exit_price is not directly in signal_data, will need to be derived or added
            "confidence_score": signal_data['confidence']
        }
    else:
        return {"symbol": symbol, "signal_strength": "N/A", "entry_price": 0.0, "exit_price": 0.0, "confidence_score": 0.0}