from sqlalchemy import Column, DateTime, Float, Integer, String

from src.core.database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime, index=True)

    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    source = Column(String, default="yahoo")

    def __repr__(self):
        return f"<MarketData(symbol={self.symbol}, time={self.timestamp}, close={self.close})>"
