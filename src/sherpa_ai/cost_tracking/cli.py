"""CLI for enhanced cost tracking."""

import argparse
import json
from datetime import datetime

from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.cost_tracking.reporting import CostReporter


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Sherpa AI Enhanced Cost Tracking CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show cost summary")
    summary_parser.add_argument("--user-id", help="Filter by user ID")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate cost reports")
    report_parser.add_argument("--type", choices=["daily", "weekly"], default="daily", help="Report type")
    report_parser.add_argument("--user-id", help="Filter by user ID")
    report_parser.add_argument("--output", help="Output file path")
    report_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    
    # Top users command
    top_users_parser = subparsers.add_parser("top-users", help="Show top users by cost")
    top_users_parser.add_argument("--limit", type=int, default=10, help="Number of users to show")
    
    # Top agents command
    top_agents_parser = subparsers.add_parser("top-agents", help="Show top agents by cost")
    top_agents_parser.add_argument("--limit", type=int, default=10, help="Number of agents to show")
    
    # Model stats command
    model_stats_parser = subparsers.add_parser("model-stats", help="Show model usage statistics")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export cost data")
    export_parser.add_argument("--output", required=True, help="Output file path")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    
    # Estimate command
    estimate_parser = subparsers.add_parser("estimate", help="Estimate cost for a model call")
    estimate_parser.add_argument("--model", required=True, help="Model name")
    estimate_parser.add_argument("--tokens", type=int, required=True, help="Number of tokens")
    
    args = parser.parse_args()
    
    if args.command == "summary":
        handle_summary_command(args)
    elif args.command == "report":
        handle_report_command(args)
    elif args.command == "top-users":
        handle_top_users_command(args)
    elif args.command == "top-agents":
        handle_top_agents_command(args)
    elif args.command == "model-stats":
        handle_model_stats_command(args)
    elif args.command == "export":
        handle_export_command(args)
    elif args.command == "estimate":
        handle_estimate_command(args)
    else:
        parser.print_help()


def handle_summary_command(args):
    """Handle the summary command."""
    tracker = UserUsageTracker()
    reporter = CostReporter(tracker)
    
    try:
        reporter.print_summary(args.user_id)
    finally:
        tracker.close_connection()


def handle_report_command(args):
    """Handle the report command."""
    tracker = UserUsageTracker()
    reporter = CostReporter(tracker)
    
    try:
        if args.type == "daily":
            report = reporter.generate_daily_report(args.user_id)
        elif args.type == "weekly":
            report = reporter.generate_weekly_report(args.user_id)
        
        output = json.dumps(report, indent=2, default=str)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Report saved to {args.output}")
        else:
            print(output)
    finally:
        tracker.close_connection()


def handle_top_users_command(args):
    """Handle the top users command."""
    tracker = UserUsageTracker()
    reporter = CostReporter(tracker)
    
    try:
        reporter.print_top_users(args.limit)
    finally:
        tracker.close_connection()


def handle_top_agents_command(args):
    """Handle the top agents command."""
    tracker = UserUsageTracker()
    reporter = CostReporter(tracker)
    
    try:
        reporter.print_top_agents(args.limit)
    finally:
        tracker.close_connection()


def handle_model_stats_command(args):
    """Handle the model stats command."""
    tracker = UserUsageTracker()
    reporter = CostReporter(tracker)
    
    try:
        reporter.print_model_stats()
    finally:
        tracker.close_connection()


def handle_export_command(args):
    """Handle the export command."""
    tracker = UserUsageTracker()
    reporter = CostReporter(tracker)
    
    try:
        data = reporter.export_data(args.format)
        
        with open(args.output, 'w') as f:
            f.write(data)
        
        print(f"Data exported to {args.output}")
    finally:
        tracker.close_connection()


def handle_estimate_command(args):
    """Handle the estimate command."""
    tracker = UserUsageTracker()
    
    try:
        estimated_cost = tracker.estimate_cost(args.model, args.tokens)
        print(f"Estimated cost for {args.tokens} tokens with {args.model}: ${estimated_cost:.4f}")
    finally:
        tracker.close_connection()


if __name__ == "__main__":
    main()
