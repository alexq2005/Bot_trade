"""
Advanced Execution Algorithms
VWAP (Volume Weighted Average Price) and TWAP (Time Weighted Average Price)
"""

from datetime import datetime, timedelta

import numpy as np


class ExecutionAlgorithms:
    """
    Advanced execution algorithms for optimal order execution.
    """

    @staticmethod
    def calculate_vwap_schedule(total_quantity, historical_volume_profile, num_slices=10):
        """
        Calculate VWAP execution schedule based on historical volume profile.

        Args:
            total_quantity: Total shares to execute
            historical_volume_profile: List of (time, volume) tuples
            num_slices: Number of execution slices

        Returns:
            List of (time, quantity) tuples
        """
        total_volume = sum(v for _, v in historical_volume_profile)

        if total_volume == 0:
            # Fallback to TWAP if no volume data
            return ExecutionAlgorithms.calculate_twap_schedule(total_quantity, num_slices)

        schedule = []
        remaining_qty = total_quantity

        for time, volume in historical_volume_profile[:num_slices]:
            # Allocate quantity proportional to volume
            slice_qty = int((volume / total_volume) * total_quantity)
            slice_qty = min(slice_qty, remaining_qty)

            if slice_qty > 0:
                schedule.append((time, slice_qty))
                remaining_qty -= slice_qty

        # Add any remaining quantity to last slice
        if remaining_qty > 0 and schedule:
            last_time, last_qty = schedule[-1]
            schedule[-1] = (last_time, last_qty + remaining_qty)

        return schedule

    @staticmethod
    def calculate_twap_schedule(total_quantity, num_slices=10, duration_minutes=60):
        """
        Calculate TWAP execution schedule (equal slices over time).

        Args:
            total_quantity: Total shares to execute
            num_slices: Number of execution slices
            duration_minutes: Total duration in minutes

        Returns:
            List of (time, quantity) tuples
        """
        slice_qty = total_quantity // num_slices
        remainder = total_quantity % num_slices

        interval = duration_minutes / num_slices
        schedule = []

        current_time = datetime.now()

        for i in range(num_slices):
            qty = slice_qty + (1 if i < remainder else 0)
            schedule.append((current_time + timedelta(minutes=i * interval), qty))

        return schedule

    @staticmethod
    def calculate_implementation_shortfall(execution_prices, benchmark_price, quantities):
        """
        Calculate implementation shortfall (slippage cost).

        Args:
            execution_prices: List of actual execution prices
            benchmark_price: Benchmark price (e.g., decision price)
            quantities: List of quantities executed at each price

        Returns:
            Implementation shortfall in basis points
        """
        total_qty = sum(quantities)

        if total_qty == 0:
            return 0

        # Weighted average execution price
        avg_execution_price = sum(p * q for p, q in zip(execution_prices, quantities)) / total_qty

        # Shortfall in basis points
        shortfall_bps = ((avg_execution_price - benchmark_price) / benchmark_price) * 10000

        return shortfall_bps

    @staticmethod
    def adaptive_vwap(total_quantity, current_volume, target_participation=0.10):
        """
        Adaptive VWAP that adjusts to real-time market volume.

        Args:
            total_quantity: Remaining quantity to execute
            current_volume: Current market volume
            target_participation: Target participation rate (default 10%)

        Returns:
            Recommended quantity for current slice
        """
        # Calculate slice quantity based on participation rate
        slice_qty = int(current_volume * target_participation)

        # Don't exceed remaining quantity
        slice_qty = min(slice_qty, total_quantity)

        return slice_qty


# Example usage
if __name__ == "__main__":
    print("=== Execution Algorithms ===\n")

    # Example: Execute 1000 shares
    total_qty = 1000

    # TWAP Schedule
    print("1. TWAP Schedule (10 slices over 60 minutes):")
    twap_schedule = ExecutionAlgorithms.calculate_twap_schedule(
        total_qty, num_slices=10, duration_minutes=60
    )
    for time, qty in twap_schedule:
        print(f"   {time.strftime('%H:%M:%S')}: {qty} shares")

    # VWAP Schedule
    print("\n2. VWAP Schedule (based on volume profile):")
    # Simulated volume profile (time, volume)
    volume_profile = [
        ("09:30", 1000),
        ("10:00", 1500),
        ("10:30", 1200),
        ("11:00", 800),
        ("11:30", 600),
        ("12:00", 400),
        ("12:30", 500),
        ("13:00", 700),
        ("13:30", 900),
        ("14:00", 1100),
    ]

    vwap_schedule = ExecutionAlgorithms.calculate_vwap_schedule(
        total_qty, volume_profile, num_slices=10
    )
    for time, qty in vwap_schedule:
        print(f"   {time}: {qty} shares")

    # Implementation Shortfall
    print("\n3. Implementation Shortfall:")
    execution_prices = [150.00, 150.05, 150.10, 149.95, 150.02]
    benchmark_price = 150.00
    quantities = [200, 200, 200, 200, 200]

    shortfall = ExecutionAlgorithms.calculate_implementation_shortfall(
        execution_prices, benchmark_price, quantities
    )
    print(f"   Benchmark Price: ${benchmark_price:.2f}")
    print(f"   Implementation Shortfall: {shortfall:.2f} bps")

    # Adaptive VWAP
    print("\n4. Adaptive VWAP:")
    current_volume = 5000
    remaining_qty = 500
    recommended_qty = ExecutionAlgorithms.adaptive_vwap(
        remaining_qty, current_volume, target_participation=0.10
    )
    print(f"   Current Volume: {current_volume}")
    print(f"   Remaining Qty: {remaining_qty}")
    print(f"   Recommended Slice: {recommended_qty} shares (10% participation)")
