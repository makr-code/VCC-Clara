#!/usr/bin/env python3
"""
Test Coverage Baseline Measurement Script

This script measures the current test coverage baseline for VCC-Clara
and identifies gaps that need to be addressed in Phase 1.

Usage:
    python scripts/measure_coverage.py
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime


def run_coverage():
    """Run pytest with coverage and generate reports."""
    print("🧪 Running tests with coverage measurement...")
    
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--cov=backend",
        "--cov=shared",
        "--cov=config",
        "--cov-report=json",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--tb=short",
        "--disable-warnings"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("⚠️  Some tests failed, but continuing with coverage analysis...")
        return True
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def analyze_coverage():
    """Analyze coverage.json and identify gaps."""
    coverage_file = Path("coverage.json")
    
    if not coverage_file.exists():
        print("❌ coverage.json not found. Run pytest with --cov-report=json first.")
        return None
    
    with open(coverage_file) as f:
        data = json.load(f)
    
    total_coverage = data['totals']['percent_covered']
    
    print(f"\n📊 Overall Coverage: {total_coverage:.2f}%")
    print("\n" + "="*60)
    
    # Analyze by module
    modules = {}
    for file_path, file_data in data['files'].items():
        if 'backend/' in file_path or 'shared/' in file_path or 'config/' in file_path:
            # Extract module name
            if 'backend/' in file_path:
                module = file_path.split('backend/')[1].split('/')[0]
                module = f"backend/{module}"
            elif 'shared/' in file_path:
                module = file_path.split('shared/')[1].split('/')[0]
                module = f"shared/{module}"
            else:
                module = 'config'
            
            if module not in modules:
                modules[module] = {
                    'covered': 0,
                    'total': 0,
                    'files': []
                }
            
            covered = file_data['summary']['covered_lines']
            total = file_data['summary']['num_statements']
            
            modules[module]['covered'] += covered
            modules[module]['total'] += total
            modules[module]['files'].append({
                'file': file_path,
                'coverage': file_data['summary']['percent_covered']
            })
    
    # Print module breakdown
    print("\n📦 Coverage by Module:")
    print("-" * 60)
    
    for module, data in sorted(modules.items()):
        if data['total'] > 0:
            coverage = (data['covered'] / data['total']) * 100
            status = "✅" if coverage >= 80 else "⚠️" if coverage >= 60 else "❌"
            print(f"{status} {module:30} {coverage:6.2f}% ({data['covered']}/{data['total']})")
    
    # Identify low coverage files
    print("\n🔍 Files with <60% Coverage (Priority for Phase 1):")
    print("-" * 60)
    
    low_coverage = []
    for module_data in modules.values():
        for file_info in module_data['files']:
            if file_info['coverage'] < 60:
                low_coverage.append(file_info)
    
    low_coverage.sort(key=lambda x: x['coverage'])
    
    for item in low_coverage[:20]:  # Top 20 lowest coverage files
        print(f"  {item['coverage']:5.1f}% - {item['file']}")
    
    if len(low_coverage) > 20:
        print(f"\n  ... and {len(low_coverage) - 20} more files")
    
    return {
        'total_coverage': total_coverage,
        'modules': modules,
        'low_coverage_files': low_coverage,
        'timestamp': datetime.now().isoformat()
    }


def generate_report(analysis):
    """Generate a baseline report."""
    if not analysis:
        return
    
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    
    report_file = report_dir / "coverage_baseline.md"
    
    with open(report_file, 'w') as f:
        f.write("# Test Coverage Baseline Report\n\n")
        f.write(f"**Generated:** {analysis['timestamp']}\n\n")
        f.write(f"**Overall Coverage:** {analysis['total_coverage']:.2f}%\n\n")
        
        f.write("## Phase 1 Target\n\n")
        f.write("- **Current:** {:.2f}%\n".format(analysis['total_coverage']))
        f.write("- **Target:** >80%\n")
        f.write("- **Gap:** {:.2f}%\n\n".format(max(0, 80 - analysis['total_coverage'])))
        
        f.write("## Coverage by Module\n\n")
        f.write("| Module | Coverage | Status |\n")
        f.write("|--------|----------|--------|\n")
        
        for module, data in sorted(analysis['modules'].items()):
            if data['total'] > 0:
                coverage = (data['covered'] / data['total']) * 100
                status = "✅ Good" if coverage >= 80 else "⚠️ Needs Work" if coverage >= 60 else "❌ Critical"
                f.write(f"| {module} | {coverage:.2f}% | {status} |\n")
        
        f.write("\n## Priority Files for Test Coverage\n\n")
        f.write("Files with <60% coverage (highest priority):\n\n")
        
        for item in analysis['low_coverage_files'][:30]:
            f.write(f"- [ ] {item['file']} ({item['coverage']:.1f}%)\n")
        
        f.write("\n## Recommendations\n\n")
        f.write("1. Focus on modules with <60% coverage first\n")
        f.write("2. Prioritize backend/training and backend/datasets (core functionality)\n")
        f.write("3. Add integration tests for critical workflows\n")
        f.write("4. Ensure all public APIs have tests\n")
    
    print(f"\n✅ Coverage baseline report saved to: {report_file}")
    
    # Also save JSON for tracking
    json_file = report_dir / "coverage_baseline.json"
    with open(json_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"✅ Coverage data saved to: {json_file}")


def main():
    """Main execution."""
    print("=" * 60)
    print("VCC-Clara Test Coverage Baseline Measurement")
    print("Phase 1: Stabilization")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path("pytest.ini").exists():
        print("❌ Error: Please run this script from the repository root")
        return 1
    
    # Run coverage
    if not run_coverage():
        print("\n⚠️  Coverage measurement had errors, but attempting analysis...")
    
    # Analyze results
    analysis = analyze_coverage()
    
    # Generate report
    generate_report(analysis)
    
    if analysis:
        print("\n" + "=" * 60)
        print(f"📊 Baseline Coverage: {analysis['total_coverage']:.2f}%")
        print(f"🎯 Phase 1 Target: >80%")
        print(f"📈 Gap to Close: {max(0, 80 - analysis['total_coverage']):.2f}%")
        print("=" * 60)
        
        if analysis['total_coverage'] < 80:
            print("\n✅ Coverage baseline established. Ready for Phase 1 test expansion.")
            return 0
        else:
            print("\n🎉 Already exceeding Phase 1 target!")
            return 0
    else:
        print("\n❌ Could not analyze coverage. Check that tests ran successfully.")
        return 1


if __name__ == "__main__":
    exit(main())
