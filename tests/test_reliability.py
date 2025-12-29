"""
Reliability testing for ktml-agent.

Tests LLM consistency by running the same input multiple times.
"""

import pytest
import time
import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

from .test_utils import git_branch_exists


@pytest.mark.reliability
@pytest.mark.slow
class TestReliability:
    """Reliability tests - run same input multiple times."""
    
    def test_git_branch_100_runs(self, agent, git_repo):
        """
        Run git branch creation 100 times to test consistency.
        
        Tracks:
        - % of valid outputs
        - % of failures
        - Categories of errors
        - Retry improvement
        """
        num_runs = 100
        max_retries = 3
        nl_input = "create a new branch called reliability-test-branch"
        
        results: List[Dict[str, Any]] = []
        error_categories = Counter()
        retry_improvements = 0
        
        print(f"\n{'='*60}")
        print(f"Running reliability test: {num_runs} iterations")
        print(f"NL Input: {nl_input}")
        print(f"{'='*60}\n")
        
        for i in range(num_runs):
            # Clean up branch from previous iteration
            import subprocess
            subprocess.run(
                ['git', 'branch', '-D', 'reliability-test-branch'],
                cwd=git_repo,
                capture_output=True
            )
            
            # First attempt
            result = agent.run(nl_input)
            
            # Track result
            success = (
                'error' not in result or result['error'] is None
            ) and result.get('exit_code') == 0
            
            result_data = {
                'iteration': i + 1,
                'success': success,
                'command': result.get('command'),
                'error': result.get('error'),
                'exit_code': result.get('exit_code'),
                'latency': result.get('total_latency', 0),
                'retries': 0
            }
            
            # Retry if failed
            if not success:
                # Categorize error
                if result.get('error'):
                    error_categories['api_error'] += 1
                elif result.get('exit_code', 0) != 0:
                    error_categories['execution_error'] += 1
                else:
                    error_categories['unknown_error'] += 1
                
                # Retry up to max_retries times
                for retry in range(max_retries):
                    time.sleep(1)  # Brief delay between retries
                    
                    retry_result = agent.run(nl_input)
                    retry_success = (
                        'error' not in retry_result or retry_result['error'] is None
                    ) and retry_result.get('exit_code') == 0
                    
                    if retry_success:
                        result_data['success'] = True
                        result_data['retries'] = retry + 1
                        retry_improvements += 1
                        break
            
            results.append(result_data)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{num_runs} runs completed")
            
            # Rate limiting - small delay between runs
            time.sleep(0.5)
        
        # Calculate statistics
        total_runs = len(results)
        first_attempt_success = sum(1 for r in results if r['success'] and r['retries'] == 0)
        final_success = sum(1 for r in results if r['success'])
        
        first_attempt_rate = (first_attempt_success / total_runs) * 100
        final_success_rate = (final_success / total_runs) * 100
        
        latencies = [r['latency'] for r in results]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Generate report
        report = {
            'test': 'Git Branch Creation - 100 Runs',
            'nl_input': nl_input,
            'total_runs': total_runs,
            'first_attempt_success': first_attempt_success,
            'first_attempt_success_rate': f"{first_attempt_rate:.1f}%",
            'final_success': final_success,
            'final_success_rate': f"{final_success_rate:.1f}%",
            'retry_improvements': retry_improvements,
            'error_categories': dict(error_categories),
            'avg_latency': f"{avg_latency:.3f}s",
            'results': results
        }
        
        # Save report
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        with open(reports_dir / "reliability_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        md_report = f"""# Reliability Test Report

## Test Configuration
- **Test**: Git Branch Creation
- **NL Input**: `{nl_input}`
- **Total Runs**: {total_runs}
- **Max Retries**: {max_retries}

## Results Summary

### Success Rates
- **First Attempt**: {first_attempt_success}/{total_runs} ({first_attempt_rate:.1f}%)
- **After Retries**: {final_success}/{total_runs} ({final_success_rate:.1f}%)
- **Retry Improvements**: {retry_improvements}

### Error Categories
"""
        
        for category, count in error_categories.items():
            md_report += f"- **{category}**: {count}\n"
        
        md_report += f"""
### Performance
- **Average Latency**: {avg_latency:.3f}s

## Detailed Results

| Iteration | Success | Retries | Latency | Error |
|-----------|---------|---------|---------|-------|
"""
        
        for r in results[:20]:  # Show first 20
            error = r.get('error', '')[:50] if r.get('error') else ''
            md_report += f"| {r['iteration']} | {'✓' if r['success'] else '✗'} | {r['retries']} | {r['latency']:.3f}s | {error} |\n"
        
        if len(results) > 20:
            md_report += f"\n*Showing first 20 of {len(results)} results. See JSON report for full details.*\n"
        
        with open(reports_dir / "reliability_report.md", 'w') as f:
            f.write(md_report)
        
        # Print summary
        print(f"\n{'='*60}")
        print("RELIABILITY TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Runs: {total_runs}")
        print(f"First Attempt Success: {first_attempt_success} ({first_attempt_rate:.1f}%)")
        print(f"Final Success: {final_success} ({final_success_rate:.1f}%)")
        print(f"Retry Improvements: {retry_improvements}")
        print(f"Average Latency: {avg_latency:.3f}s")
        print(f"{'='*60}\n")
        
        # Assertions
        assert first_attempt_rate >= 80, \
            f"First attempt success rate too low: {first_attempt_rate:.1f}% (expected >=80%)"
        assert final_success_rate >= 90, \
            f"Final success rate too low: {final_success_rate:.1f}% (expected >=90%)"
