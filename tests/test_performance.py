"""
Performance testing for ktml-agent.

Tracks and reports latency metrics.
"""

import pytest
import json
import statistics
from pathlib import Path
from typing import List


@pytest.mark.performance
class TestPerformance:
    """Performance benchmarking tests."""
    
    def test_latency_benchmarks(self, agent, git_repo):
        """
        Run multiple queries and track latency metrics.
        
        Reports:
        - LLM response latency
        - Command execution latency
        - Total end-to-end latency
        - Averages + percentiles (p50, p95, p99)
        """
        test_cases = [
            "create a new branch called perf-test",
            "list all files in the current directory",
            "show the git status",
            "create a file called test.txt with content 'Hello World'",
            "count the number of files in this directory",
        ]
        
        results = []
        
        print(f"\n{'='*60}")
        print("PERFORMANCE BENCHMARKING")
        print(f"{'='*60}\n")
        
        for i, nl_input in enumerate(test_cases, 1):
            print(f"Test {i}/{len(test_cases)}: {nl_input}")
            
            result = agent.run(nl_input)
            
            results.append({
                'nl_input': nl_input,
                'llm_latency': result.get('llm_latency', 0),
                'execution_latency': result.get('execution_latency', 0),
                'total_latency': result.get('total_latency', 0),
                'command': result.get('command', ''),
                'success': result.get('exit_code') == 0
            })
            
            print(f"  LLM: {result.get('llm_latency', 0):.3f}s | "
                  f"Exec: {result.get('execution_latency', 0):.3f}s | "
                  f"Total: {result.get('total_latency', 0):.3f}s")
        
        # Calculate statistics
        llm_latencies = [r['llm_latency'] for r in results]
        exec_latencies = [r['execution_latency'] for r in results]
        total_latencies = [r['total_latency'] for r in results]
        
        def calc_stats(latencies: List[float]) -> dict:
            """Calculate statistics for latency list."""
            if not latencies:
                return {}
            
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            
            return {
                'count': n,
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'stdev': statistics.stdev(latencies) if n > 1 else 0,
                'min': min(latencies),
                'max': max(latencies),
                'p50': sorted_latencies[int(n * 0.50)],
                'p95': sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0],
                'p99': sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0],
            }
        
        llm_stats = calc_stats(llm_latencies)
        exec_stats = calc_stats(exec_latencies)
        total_stats = calc_stats(total_latencies)
        
        # Generate report
        report = {
            'test': 'Performance Benchmarking',
            'num_queries': len(test_cases),
            'llm_latency': llm_stats,
            'execution_latency': exec_stats,
            'total_latency': total_stats,
            'detailed_results': results
        }
        
        # Save JSON report
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        with open(reports_dir / "performance_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        md_report = f"""# Performance Benchmarking Report

## Test Configuration
- **Number of Queries**: {len(test_cases)}

## Latency Metrics

### LLM Response Latency
| Metric | Value |
|--------|-------|
| Mean | {llm_stats['mean']:.3f}s |
| Median (p50) | {llm_stats['median']:.3f}s |
| p95 | {llm_stats['p95']:.3f}s |
| p99 | {llm_stats['p99']:.3f}s |
| Min | {llm_stats['min']:.3f}s |
| Max | {llm_stats['max']:.3f}s |
| Std Dev | {llm_stats['stdev']:.3f}s |

### Command Execution Latency
| Metric | Value |
|--------|-------|
| Mean | {exec_stats['mean']:.3f}s |
| Median (p50) | {exec_stats['median']:.3f}s |
| p95 | {exec_stats['p95']:.3f}s |
| p99 | {exec_stats['p99']:.3f}s |
| Min | {exec_stats['min']:.3f}s |
| Max | {exec_stats['max']:.3f}s |
| Std Dev | {exec_stats['stdev']:.3f}s |

### Total End-to-End Latency
| Metric | Value |
|--------|-------|
| Mean | {total_stats['mean']:.3f}s |
| Median (p50) | {total_stats['median']:.3f}s |
| p95 | {total_stats['p95']:.3f}s |
| p99 | {total_stats['p99']:.3f}s |
| Min | {total_stats['min']:.3f}s |
| Max | {total_stats['max']:.3f}s |
| Std Dev | {total_stats['stdev']:.3f}s |

## Detailed Results

| Query | LLM (s) | Exec (s) | Total (s) | Success |
|-------|---------|----------|-----------|---------|
"""
        
        for r in results:
            query_short = r['nl_input'][:50] + '...' if len(r['nl_input']) > 50 else r['nl_input']
            md_report += f"| {query_short} | {r['llm_latency']:.3f} | {r['execution_latency']:.3f} | {r['total_latency']:.3f} | {'✓' if r['success'] else '✗'} |\n"
        
        md_report += """
## Performance Analysis

"""
        
        # Add analysis
        if total_stats['p95'] < 2.0:
            md_report += "✅ **Excellent**: p95 latency under 2 seconds\n"
        elif total_stats['p95'] < 3.0:
            md_report += "✓ **Good**: p95 latency under 3 seconds\n"
        else:
            md_report += "⚠️ **Needs Improvement**: p95 latency over 3 seconds\n"
        
        if llm_stats['mean'] > total_stats['mean'] * 0.8:
            md_report += "\n**Note**: LLM latency dominates total latency. Consider caching optimization.\n"
        
        with open(reports_dir / "performance_report.md", 'w') as f:
            f.write(md_report)
        
        # Print summary
        print(f"\n{'='*60}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Total Latency:")
        print(f"  Mean: {total_stats['mean']:.3f}s")
        print(f"  Median (p50): {total_stats['median']:.3f}s")
        print(f"  p95: {total_stats['p95']:.3f}s")
        print(f"  p99: {total_stats['p99']:.3f}s")
        print(f"\nLLM Latency:")
        print(f"  Mean: {llm_stats['mean']:.3f}s")
        print(f"  p95: {llm_stats['p95']:.3f}s")
        print(f"\nExecution Latency:")
        print(f"  Mean: {exec_stats['mean']:.3f}s")
        print(f"  p95: {exec_stats['p95']:.3f}s")
        print(f"{'='*60}\n")
        
        # Assertions
        assert total_stats['p95'] < 5.0, \
            f"p95 latency too high: {total_stats['p95']:.3f}s (expected <5s)"
        assert total_stats['mean'] < 3.0, \
            f"Mean latency too high: {total_stats['mean']:.3f}s (expected <3s)"
