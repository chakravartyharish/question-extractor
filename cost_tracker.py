#!/usr/bin/env python3
"""
Cost tracking module for monitoring API usage and expenses.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CostTracker:
    """Track API calls and token usage for cost estimation."""
    
    total_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    
    # Perplexity pricing (as of 2025)
    # Input: ~$1 per 1M tokens
    # Output: ~$5 per 1M tokens
    INPUT_COST_PER_TOKEN: float = 1.0 / 1_000_000
    OUTPUT_COST_PER_TOKEN: float = 5.0 / 1_000_000
    
    def record_call(
        self,
        input_tokens: int,
        output_tokens: int,
        success: bool = True
    ) -> None:
        """
        Record an API call with token counts.
        
        Args:
            input_tokens: Number of input (prompt) tokens
            output_tokens: Number of output (completion) tokens
            success: Whether the call was successful
        """
        self.total_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
    
    def estimate_input_cost(self) -> float:
        """Calculate estimated cost for input tokens."""
        return self.input_tokens * self.INPUT_COST_PER_TOKEN
    
    def estimate_output_cost(self) -> float:
        """Calculate estimated cost for output tokens."""
        return self.output_tokens * self.OUTPUT_COST_PER_TOKEN
    
    def estimate_cost(self) -> float:
        """
        Calculate total estimated cost in USD.
        
        Returns:
            Total estimated cost in dollars
        """
        return self.estimate_input_cost() + self.estimate_output_cost()
    
    def summary(self) -> Dict:
        """
        Generate summary dictionary.
        
        Returns:
            Dictionary with all tracking metrics
        """
        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.input_tokens + self.output_tokens,
            'estimated_cost_usd': round(self.estimate_cost(), 4),
            'input_cost_usd': round(self.estimate_input_cost(), 4),
            'output_cost_usd': round(self.estimate_output_cost(), 4),
        }
    
    def print_summary(self) -> None:
        """Print formatted summary to console."""
        summary = self.summary()
        
        print("\n" + "="*60)
        print("💰 API COST SUMMARY")
        print("="*60)
        print(f"Total API Calls:     {summary['total_calls']}")
        print(f"  ✅ Successful:     {summary['successful_calls']}")
        print(f"  ❌ Failed:         {summary['failed_calls']}")
        print(f"\nToken Usage:")
        print(f"  Input tokens:      {summary['input_tokens']:,}")
        print(f"  Output tokens:     {summary['output_tokens']:,}")
        print(f"  Total tokens:      {summary['total_tokens']:,}")
        print(f"\nCost Estimate:")
        print(f"  Input cost:        ${summary['input_cost_usd']:.4f}")
        print(f"  Output cost:       ${summary['output_cost_usd']:.4f}")
        print(f"  Total cost:        ${summary['estimated_cost_usd']:.4f}")
        print("="*60)
        
        # Add warning if cost is high
        if summary['estimated_cost_usd'] > 10.0:
            print("⚠️  WARNING: Estimated cost exceeds $10.00")
        elif summary['estimated_cost_usd'] > 5.0:
            print("⚠️  High cost detected. Consider using smaller batches.")
        
        print()
    
    @staticmethod
    def estimate_tokens_from_text(text: str) -> int:
        """
        Rough estimation of tokens from text.
        Uses word count * 1.3 as approximation.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        words = len(text.split())
        return int(words * 1.3)
