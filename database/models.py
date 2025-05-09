from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class OHLCVData(Base):
    """Model for OHLCV cryptocurrency data"""
    __tablename__ = 'ohlcv_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, default='1d', index=True)  # '1m', '5m', '1h', '1d'
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<OHLCVData(symbol='{self.symbol}', timeframe='{self.timeframe}', timestamp='{self.timestamp}')>"

class NewsData(Base):
    """Model for cryptocurrency news articles"""
    __tablename__ = 'news_data'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    published_date = Column(DateTime, nullable=False, index=True)
    link = Column(String(512), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=False)
    collected_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<NewsData(title='{self.title}', published_date='{self.published_date}')>"

class SocialData(Base):
    """Model for social media posts about cryptocurrencies"""
    __tablename__ = 'social_data'
    
    id = Column(String(50), primary_key=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)
    retweet_count = Column(Integer, nullable=False, default=0)
    like_count = Column(Integer, nullable=False, default=0)
    reply_count = Column(Integer, nullable=False, default=0)
    author_id = Column(String(50), nullable=True)
    lang = Column(String(10), nullable=True)
    query = Column(String(50), nullable=False)
    platform = Column(String(20), nullable=False)
    collected_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<SocialData(platform='{self.platform}', created_at='{self.created_at}')>"

class SentimentData(Base):
    """Model for sentiment analysis results"""
    __tablename__ = 'sentiment_data'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(String(50), nullable=False, index=True)
    source = Column(String(20), nullable=False)  # 'news' or 'social'
    score = Column(Float, nullable=False)  # -1.0 to 1.0
    magnitude = Column(Float, nullable=False)  # 0.0 to +infinity
    provider = Column(String(20), nullable=False)  # 'google_nlp', 'basic', etc.
    analyzed_at = Column(DateTime, nullable=False, index=True)
    
    def __repr__(self):
        return f"<SentimentData(item_id='{self.item_id}', score={self.score})>"

class TechnicalIndicators(Base):
    """Model for technical indicators calculated for cryptocurrencies"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    ema_200 = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    support = Column(Float, nullable=True)
    resistance = Column(Float, nullable=True)
    trend_slope = Column(Float, nullable=True)
    trend = Column(String(20), nullable=True)
    
    def __repr__(self):
        return f"<TechnicalIndicators(symbol='{self.symbol}', timestamp='{self.timestamp}')>"

class Alert(Base):
    """Model for user-configured price and indicator alerts"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # 'price', 'indicator', etc.
    condition = Column(String(10), nullable=False)  # 'above', 'below', 'crosses', etc.
    value = Column(Float, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    triggered = Column(Boolean, nullable=False, default=False)
    last_checked = Column(DateTime, nullable=True)
    last_triggered = Column(DateTime, nullable=True)
    notification_sent = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)
    # New fields for enhanced trigger functionality
    trigger_count = Column(Integer, nullable=False, default=0)
    daily_trigger_count = Column(Integer, nullable=False, default=0)
    daily_count_reset = Column(DateTime, nullable=True)
    recurring = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<Alert(symbol='{self.symbol}', type='{self.alert_type}')>"

class BacktestResults(Base):
    """Model for backtest results summary"""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    strategy = Column(String(50), nullable=False)
    exchange = Column(String(20), nullable=False)
    period_days = Column(Integer, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    annual_return = Column(Float, nullable=False)
    annual_volatility = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    trades = relationship("BacktestTrade", backref="backtest")
    
    def __repr__(self):
        return f"<BacktestResults(symbol='{self.symbol}', strategy='{self.strategy}')>"

class BacktestTrade(Base):
    """Model for individual trades from backtests"""
    __tablename__ = 'backtest_trades'
    
    id = Column(Integer, primary_key=True)
    backtest_id = Column(Integer, ForeignKey('backtest_results.id'), nullable=False)
    entry_date = Column(DateTime, nullable=True)
    entry_price = Column(Float, nullable=True)
    exit_date = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<BacktestTrade(backtest_id={self.backtest_id}, pnl={self.pnl})>"

class CustomSource(Base):
    """Model for user-defined custom data sources"""
    __tablename__ = 'custom_sources'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(20), nullable=False)  # 'API', 'CSV', etc.
    config = Column(Text, nullable=False)  # JSON configuration
    enabled = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<CustomSource(name='{self.name}', type='{self.type}')>"

class CustomData(Base):
    """Model for data from custom sources"""
    __tablename__ = 'custom_data'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(String(50), ForeignKey('custom_sources.id'), nullable=False)
    data = Column(Text, nullable=False)  # JSON data
    collected_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<CustomData(source_id='{self.source_id}', collected_at='{self.collected_at}')>"

class LogEntry(Base):
    """Model for application logs"""
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(String(10), nullable=False, index=True)
    module = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<LogEntry(timestamp='{self.timestamp}', level='{self.level}')>"
