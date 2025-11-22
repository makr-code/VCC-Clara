#!/usr/bin/env python3
"""
Knowledge Gap Management CLI

Query and manage knowledge gaps detected during LoRA adapter training.
Supports both JSONL file storage and PostgreSQL database.

Usage:
    # List all open gaps (file-based)
    python scripts/clara_knowledge_gaps.py list

    # List gaps from PostgreSQL
    python scripts/clara_knowledge_gaps.py list --postgres

    # Show high priority gaps
    python scripts/clara_knowledge_gaps.py priority --top 10 --postgres

    # Show gaps for specific domain and system
    python scripts/clara_knowledge_gaps.py list --domain verwaltungsrecht --system clara --postgres

    # Show statistics
    python scripts/clara_knowledge_gaps.py stats --postgres

    # Mark gap as resolved
    python scripts/clara_knowledge_gaps.py resolve gap-123 --notes "Added training data" --postgres
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.adapters import get_knowledge_gap_database, GapSeverity


def get_database(use_postgres: bool = False, system_filter: Optional[str] = None):
    """
    Get knowledge gap database instance
    
    Args:
        use_postgres: Use PostgreSQL instead of file
        system_filter: System source filter (clara/veritas/covina)
        
    Returns:
        Database instance and system source enum
    """
    if use_postgres:
        try:
            from shared.adapters import get_knowledge_gap_pg_database, SystemSource
            gap_db = get_knowledge_gap_pg_database()
            
            # Convert system filter to enum
            system_source = None
            if system_filter:
                system_source = SystemSource(system_filter.lower())
            
            return gap_db, system_source
        except Exception as e:
            print(f"❌ PostgreSQL not available: {e}")
            print("Falling back to file-based database...")
            return get_knowledge_gap_database(), None
    else:
        return get_knowledge_gap_database(), None


def list_gaps(
    domain: Optional[str] = None,
    severity: Optional[str] = None,
    status: str = "open",
    use_postgres: bool = False,
    system_filter: Optional[str] = None
):
    """List knowledge gaps with filters"""
    gap_db, system_source = get_database(use_postgres, system_filter)
    
    # Convert severity string to enum
    severity_enum = GapSeverity(severity) if severity else None
    
    # Get gaps with appropriate parameters
    if use_postgres and hasattr(gap_db, 'get_gaps'):
        gaps = gap_db.get_gaps(
            domain=domain,
            severity=severity_enum,
            status=status,
            system_source=system_source
        )
    else:
        gaps = gap_db.get_gaps(
            domain=domain,
            severity=severity_enum,
            status=status
    )
    
    if not gaps:
        print("No knowledge gaps found with the specified filters.")
        return
    
    print(f"\n{'=' * 80}")
    print(f"Knowledge Gaps ({len(gaps)} found)")
    print(f"{'=' * 80}\n")
    
    for i, gap in enumerate(gaps, 1):
        priority = gap.calculate_priority()
        print(f"{i}. {gap.gap_id}")
        print(f"   Domain: {gap.domain}")
        print(f"   Topic: {gap.topic}")
        print(f"   Severity: {gap.severity.value} | Priority: {priority:.1f}/100")
        print(f"   Source: {gap.source.value}")
        if gap.adapter_id:
            print(f"   Adapter: {gap.adapter_id}")
        if gap.evaluation_score is not None:
            print(f"   Evaluation Score: {gap.evaluation_score:.1f}/100")
        if gap.suggested_data_query:
            print(f"   Suggested Query: {gap.suggested_data_query}")
        if gap.tags:
            print(f"   Tags: {', '.join(gap.tags)}")
        print(f"   Status: {gap.status}")
        print(f"   Detected: {gap.detected_at}")
        print()


def show_priority_gaps(top_n: int = 10, use_postgres: bool = False, system_filter: Optional[str] = None):
    """Show highest priority gaps"""
    gap_db, system_source = get_database(use_postgres, system_filter)
    
    if use_postgres and hasattr(gap_db, 'get_priority_gaps'):
        gaps = gap_db.get_priority_gaps(top_n=top_n, system_source=system_source)
    else:
        gaps = gap_db.get_priority_gaps(top_n=top_n)
    
    if not gaps:
        print("No open knowledge gaps found.")
        return
    
    print(f"\n{'=' * 80}")
    print(f"Top {len(gaps)} Priority Knowledge Gaps")
    print(f"{'=' * 80}\n")
    
    for i, gap in enumerate(gaps, 1):
        priority = gap.calculate_priority()
        print(f"{i}. [{priority:.1f}] {gap.gap_id}")
        print(f"   Topic: {gap.topic}")
        print(f"   Domain: {gap.domain} | Severity: {gap.severity.value}")
        if gap.adapter_id:
            print(f"   Adapter: {gap.adapter_id}")
        if gap.evaluation_score is not None:
            print(f"   Score: {gap.evaluation_score:.1f}/100")
        print(f"   Query: {gap.suggested_data_query or 'N/A'}")
        print()


def show_statistics(use_postgres: bool = False, system_filter: Optional[str] = None):
    """Show knowledge gap statistics"""
    gap_db, system_source = get_database(use_postgres, system_filter)
    
    if use_postgres and hasattr(gap_db, 'get_statistics'):
        stats = gap_db.get_statistics(system_source=system_source)
    else:
        stats = gap_db.get_statistics()
    
    print(f"\n{'=' * 80}")
    print("Knowledge Gap Statistics")
    if use_postgres and system_filter:
        print(f"(System: {system_filter})")
    print(f"{'=' * 80}\n")
    
    print(f"Total Gaps: {stats.get('total_gaps', 0)}")
    print(f"Open: {stats.get('open_gaps', 0)}")
    print(f"Resolved: {stats.get('resolved_gaps', 0)}")
    print(f"In Progress: {stats.get('in_progress', 0)}")
    print(f"Average Score: {stats.get('avg_score', 0):.1f}/100")
    
    print(f"\nBy Severity:")
    for severity, count in stats.get('by_severity', {}).items():
        print(f"  {severity}: {count}")
    
    print(f"\nBy Domain:")
    for domain, count in stats.get('by_domain', {}).items():
        print(f"  {domain}: {count}")
    
    print(f"\nBy Source:")
    for source, count in stats.get('by_source', {}).items():
        print(f"  {source}: {count}")
    
    # Show system breakdown if not filtering by system
    if use_postgres and not system_filter and 'by_system' in stats:
        print(f"\nBy System:")
        for system, count in stats.get('by_system', {}).items():
            print(f"  {system}: {count}")
    
    print()


def resolve_gap(gap_id: str, notes: Optional[str] = None, use_postgres: bool = False):
    """Mark gap as resolved"""
    gap_db, _ = get_database(use_postgres)
    
    gap_db.update_gap_status(
        gap_id=gap_id,
        status="resolved",
        resolution_notes=notes
    )
    
    print(f"✅ Gap marked as resolved: {gap_id}")
    if notes:
        print(f"   Notes: {notes}")


def export_gaps(output_path: str, domain: Optional[str] = None, use_postgres: bool = False, system_filter: Optional[str] = None):
    """Export gaps to file for data collection"""
    import json
    
    gap_db, system_source = get_database(use_postgres, system_filter)
    
    if use_postgres and hasattr(gap_db, 'get_gaps'):
        gaps = gap_db.get_gaps(domain=domain, status="open", system_source=system_source)
    else:
        gaps = gap_db.get_gaps(domain=domain, status="open")
    
    # Export with suggested queries
    data = []
    for gap in gaps:
        data.append({
            "gap_id": gap.gap_id,
            "domain": gap.domain,
            "topic": gap.topic,
            "severity": gap.severity.value,
            "suggested_query": gap.suggested_data_query,
            "priority": gap.calculate_priority(),
            "tags": gap.tags
        })
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(data)} gaps to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Knowledge Gap Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all open gaps
  python scripts/clara_knowledge_gaps.py list

  # Show gaps for specific domain
  python scripts/clara_knowledge_gaps.py list --domain verwaltungsrecht

  # Show only critical gaps
  python scripts/clara_knowledge_gaps.py list --severity critical

  # Show top priority gaps
  python scripts/clara_knowledge_gaps.py priority --top 10

  # Show statistics
  python scripts/clara_knowledge_gaps.py stats

  # Mark gap as resolved
  python scripts/clara_knowledge_gaps.py resolve gap-123 --notes "Added training data"

  # Export gaps for data collection
  python scripts/clara_knowledge_gaps.py export gaps.json --domain verwaltungsrecht
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List knowledge gaps')
    list_parser.add_argument('--domain', type=str, help='Filter by domain')
    list_parser.add_argument(
        '--severity',
        type=str,
        choices=['critical', 'high', 'medium', 'low'],
        help='Filter by severity'
    )
    list_parser.add_argument(
        '--status',
        type=str,
        default='open',
        help='Filter by status (default: open)'
    )
    list_parser.add_argument(
        '--postgres',
        action='store_true',
        help='Use PostgreSQL database'
    )
    list_parser.add_argument(
        '--system',
        type=str,
        choices=['clara', 'veritas', 'covina'],
        help='Filter by system source (only with --postgres)'
    )
    
    # Priority command
    priority_parser = subparsers.add_parser('priority', help='Show priority gaps')
    priority_parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Number of top gaps to show (default: 10)'
    )
    priority_parser.add_argument(
        '--postgres',
        action='store_true',
        help='Use PostgreSQL database'
    )
    priority_parser.add_argument(
        '--system',
        type=str,
        choices=['clara', 'veritas', 'covina'],
        help='Filter by system source (only with --postgres)'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument(
        '--postgres',
        action='store_true',
        help='Use PostgreSQL database'
    )
    stats_parser.add_argument(
        '--system',
        type=str,
        choices=['clara', 'veritas', 'covina'],
        help='Filter by system source (only with --postgres)'
    )
    
    # Resolve command
    resolve_parser = subparsers.add_parser('resolve', help='Mark gap as resolved')
    resolve_parser.add_argument('gap_id', type=str, help='Gap ID to resolve')
    resolve_parser.add_argument('--notes', type=str, help='Resolution notes')
    resolve_parser.add_argument(
        '--postgres',
        action='store_true',
        help='Use PostgreSQL database'
    )
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export gaps to file')
    export_parser.add_argument('output', type=str, help='Output file path')
    export_parser.add_argument('--domain', type=str, help='Filter by domain')
    export_parser.add_argument(
        '--postgres',
        action='store_true',
        help='Use PostgreSQL database'
    )
    export_parser.add_argument(
        '--system',
        type=str,
        choices=['clara', 'veritas', 'covina'],
        help='Filter by system source (only with --postgres)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'list':
        list_gaps(
            domain=args.domain,
            severity=args.severity,
            status=args.status,
            use_postgres=args.postgres,
            system_filter=args.system
        )
    
    elif args.command == 'priority':
        show_priority_gaps(
            top_n=args.top,
            use_postgres=args.postgres,
            system_filter=args.system
        )
    
    elif args.command == 'stats':
        show_statistics(
            use_postgres=args.postgres,
            system_filter=args.system
        )
    
    elif args.command == 'resolve':
        resolve_gap(
            gap_id=args.gap_id,
            notes=args.notes,
            use_postgres=args.postgres
        )
    
    elif args.command == 'export':
        export_gaps(
            output_path=args.output,
            domain=args.domain,
            use_postgres=args.postgres,
            system_filter=args.system
        )


if __name__ == "__main__":
    main()
