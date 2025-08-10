import pandas as pd
import numpy as np
from loguru import logger

def calculate_node_features(klines_data: dict, order_book_data: dict, funding_rate: float):
    """
    Calculates node features for a given trading pair.
    klines_data: list of kline data (e.g., from BinanceClient.get_klines)
    order_book_data: order book depth data (e.g., from BinanceClient.get_order_book)
    funding_rate: latest funding rate
    """
    if not klines_data or len(klines_data) < 200: # Need enough data for RSI, volatility
        logger.warning("Insufficient klines data for feature calculation.")
        return None

    df = pd.DataFrame(klines_data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

    # Logarithmic returns
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))

    # Price features
    log_return_1h = df['log_return'].iloc[-1]
    log_return_4h = np.log(df['close'].iloc[-1] / df['close'].iloc[-5]) if len(df) >= 5 else 0
    log_return_12h = np.log(df['close'].iloc[-1] / df['close'].iloc[-13]) if len(df) >= 13 else 0
    log_return_24h = np.log(df['close'].iloc[-1] / df['close'].iloc[-25]) if len(df) >= 25 else 0

    # Volatility (standard deviation of returns)
    volatility_24h = df['log_return'].iloc[-24:].std() if len(df) >= 24 else 0

    # RSI (Relative Strength Index)
    # Simplified RSI calculation for demonstration
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1] if not pd.isna(rs.iloc[-1]) else 50 # Default to 50 if NaN

    # Volume features
    avg_volume_24h = df['volume'].iloc[-24:].mean() if len(df) >= 24 else 0
    volume_ratio = df['volume'].iloc[-1] / avg_volume_24h if avg_volume_24h > 0 else 0

    # Order book features
    best_ask = float(order_book_data['asks'][0][0]) if order_book_data and order_book_data['asks'] else 0
    best_bid = float(order_book_data['bids'][0][0]) if order_book_data and order_book_data['bids'] else 0
    spread = best_ask - best_bid if best_ask and best_bid else 0

    total_bid_volume = sum(float(b[1]) for b in order_book_data['bids']) if order_book_data and order_book_data['bids'] else 0
    total_ask_volume = sum(float(a[1]) for a in order_book_data['asks']) if order_book_data and order_book_data['asks'] else 0
    
    order_book_imbalance = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume) if (total_bid_volume + total_ask_volume) > 0 else 0

    # Funding rate feature
    funding_rate_feature = funding_rate if funding_rate is not None else 0

    features = [
        log_return_1h, log_return_4h, log_return_12h, log_return_24h,
        volatility_24h, rsi, volume_ratio, spread, order_book_imbalance,
        funding_rate_feature
    ]
    logger.debug(f"Calculated features: {features}")
    return features

def calculate_edge_weights(all_klines_data: dict):
    """
    Calculates Pearson correlation as edge weights between trading pairs.
    all_klines_data: dict where keys are symbols and values are klines data.
    """
    logger.info("Calculating edge weights (correlations)...")
    log_returns = {}
    for symbol, klines_data in all_klines_data.items():
        if klines_data and len(klines_data) >= 100: # Need at least 100 hours for correlation
            df = pd.DataFrame(klines_data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                'taker_buy_quote_asset_volume', 'ignore'
            ])
            df['close'] = df['close'].astype(float)
            df['log_return'] = np.log(df['close'] / df['close'].shift(1))
            log_returns[symbol] = df['log_return'].iloc[-100:] # Last 100 hours

    if len(log_returns) < 2:
        logger.warning("Insufficient data to calculate correlations between pairs.")
        return {}

    returns_df = pd.DataFrame(log_returns)
    correlation_matrix = returns_df.corr(method='pearson')
    
    edge_weights = {}
    symbols = list(log_returns.keys())
    for i in range(len(symbols)):
        for j in range(i + 1, len(symbols)):
            s1 = symbols[i]
            s2 = symbols[j]
            if s1 in correlation_matrix.index and s2 in correlation_matrix.columns:
                correlation = correlation_matrix.loc[s1, s2]
                if not pd.isna(correlation):
                    edge_weights[(s1, s2)] = correlation
                    edge_weights[(s2, s1)] = correlation # Symmetric
    logger.info(f"Calculated {len(edge_weights) // 2} unique edge weights.")
    return edge_weights
