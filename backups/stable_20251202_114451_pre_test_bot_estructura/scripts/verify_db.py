"""
Script to verify database contents.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import SessionLocal
from src.models.market_data import MarketData
from sqlalchemy import func

def verify_database():
    """
    Verify database contents and show statistics.
    """
    db = SessionLocal()
    
    try:
        # Total records
        total = db.query(MarketData).count()
        print(f"Total records in database: {total}")
        print()
        
        # Records per symbol
        print("Records per symbol:")
        symbols = db.query(
            MarketData.symbol,
            func.count(MarketData.id).label('count'),
            func.min(MarketData.timestamp).label('first_date'),
            func.max(MarketData.timestamp).label('last_date')
        ).group_by(MarketData.symbol).all()
        
        for symbol, count, first_date, last_date in symbols:
            print(f"  {symbol:10} {count:4} records  ({first_date.date()} to {last_date.date()})")
        
        print()
        
        # Sample data for AAPL
        print("Sample data (AAPL - last 5 records):")
        samples = db.query(MarketData).filter(
            MarketData.symbol == "AAPL"
        ).order_by(MarketData.timestamp.desc()).limit(5).all()
        
        for record in samples:
            print(f"  {record.timestamp.date()} | Close: ${record.close:.2f} | Volume: {record.volume:,.0f}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_database()
