"""
API REST Principal usando FastAPI
"""
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import os

from src.core.logger import get_logger
from src.services.health_monitor import HealthMonitor, check_system_health

logger = get_logger("api")

# Crear aplicación FastAPI
app = FastAPI(
    title="IOL Quantum AI Trading API",
    description="API REST para el sistema de trading algorítmico",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Modelos Pydantic
class HealthResponse(BaseModel):
    overall_status: str
    timestamp: str
    components: List[Dict]
    metrics: Dict
    recommendations: List[str]


class TradeRequest(BaseModel):
    symbol: str
    quantity: int
    price: float
    side: str  # 'buy' o 'sell'


class TradeResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    message: str


class PredictionRequest(BaseModel):
    symbol: str


class PredictionResponse(BaseModel):
    symbol: str
    signal: str
    predicted_price: float
    current_price: float
    change_pct: float
    confidence: float


# Endpoints
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "IOL Quantum AI Trading API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Verifica la salud del sistema
    """
    try:
        health = check_system_health()
        return {
            "overall_status": health.overall_status,
            "timestamp": health.timestamp.isoformat(),
            "components": [
                {
                    "component": c.component,
                    "status": c.status,
                    "message": c.message,
                    "response_time_ms": c.response_time_ms
                }
                for c in health.components
            ],
            "metrics": health.metrics,
            "recommendations": health.recommendations
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/predict/{symbol}", response_model=PredictionResponse)
async def get_prediction(symbol: str):
    """
    Obtiene una predicción para un símbolo
    """
    try:
        from src.services.prediction_service import PredictionService
        
        service = PredictionService()
        result = service.generate_signal(symbol, threshold=2.0)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"No se pudo generar predicción para {symbol}")
        
        return {
            "symbol": symbol,
            "signal": result.get("signal", "HOLD"),
            "predicted_price": result.get("predicted_price", 0.0),
            "current_price": result.get("current_price", 0.0),
            "change_pct": result.get("change_pct", 0.0),
            "confidence": result.get("confidence", 0.0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo predicción para {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/trade", response_model=TradeResponse)
async def execute_trade(trade: TradeRequest, credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Ejecuta una orden de trading
    
    Requiere autenticación
    """
    try:
        # TODO: Implementar autenticación real
        # token = credentials.credentials
        # if not verify_token(token):
        #     raise HTTPException(status_code=401, detail="Token inválido")
        
        # Validar orden
        from src.core.security import get_order_validator, get_audit_logger
        
        validator = get_order_validator()
        audit = get_audit_logger()
        
        # Obtener capital actual (simplificado)
        from src.connectors.iol_client import IOLClient
        iol_client = IOLClient()
        capital = iol_client.get_available_balance()
        
        is_valid, error_msg = validator.validate_order(
            trade.symbol,
            trade.quantity,
            trade.price,
            capital,
            trade.side
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Ejecutar orden
        result = iol_client.place_order(
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=trade.price,
            side=trade.side
        )
        
        # Log de auditoría
        audit.log_operation(
            "ORDER_EXECUTED",
            {
                "symbol": trade.symbol,
                "quantity": trade.quantity,
                "price": trade.price,
                "side": trade.side,
                "order_id": result.get("numeroOperacion")
            }
        )
        
        if result.get("error"):
            return {
                "success": False,
                "message": result.get("error")
            }
        
        return {
            "success": True,
            "order_id": result.get("numeroOperacion"),
            "message": "Orden ejecutada correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/portfolio")
async def get_portfolio():
    """
    Obtiene el portafolio actual
    """
    try:
        from src.services.portfolio_persistence import load_portfolio
        
        portfolio = load_portfolio()
        return {
            "portfolio": portfolio,
            "total_positions": len(portfolio) if portfolio else 0
        }
    except Exception as e:
        logger.error(f"Error obteniendo portafolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics")
async def get_metrics():
    """
    Obtiene métricas del sistema
    """
    try:
        from src.services.health_monitor import HealthMonitor
        
        monitor = HealthMonitor()
        health = monitor.check_all()
        
        return {
            "health": health.overall_status,
            "components": len(health.components),
            "metrics": health.metrics,
            "timestamp": health.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

