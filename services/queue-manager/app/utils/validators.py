from fastapi import HTTPException

VALID_TYPES = {
    "api_candles_1m",
    "api_candles_5m",
    "ws_candles_1m",
    "ws_trades",
    "ws_orderbook",
    "graph_from_candles",
    "graph_from_trades",
}

def validate_type(type_: str):
    if type_ not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Недопустимый тип данных: {type_}")
