"""CLI for cost tracking."""

import argparse
import json

from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.cost_tracking.reporting import CostReporter


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Sherpa AI Cost Tracking CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show cost summary")
    summary_parser.add_argument("--user-id", help="Filter by user ID")
    
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
    estimate_parser.add_argument("--input-tokens", type=int, required=True, help="Number of input tokens")
    estimate_parser.add_argument("--output-tokens", type=int, required=True, help="Number of output tokens")
    
    # Usage metadata command
    metadata_parser = subparsers.add_parser("metadata", help="Show usage metadata details")
    metadata_parser.add_argument("--limit", type=int, default=10, help="Number of records to show")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize tracker and reporter
    tracker = UserUsageTracker()
    reporter = CostReporter(tracker)
    
    try:
        if args.command == "summary":
            handle_summary_command(tracker, args)
        elif args.command == "top-users":
            handle_top_users_command(reporter, args)
        elif args.command == "top-agents":
            handle_top_agents_command(reporter, args)
        elif args.command == "model-stats":
            handle_model_stats_command(reporter, args)
        elif args.command == "export":
            handle_export_command(reporter, args)
        elif args.command == "estimate":
            handle_estimate_command(tracker, args)
        elif args.command == "metadata":
            handle_metadata_command(tracker, args)
    finally:
        tracker.close_connection()


def handle_summary_command(tracker, args):
    """Handle summary command."""
    summary = tracker.get_cost_summary(args.user_id)
    print(f"Cost Summary{' for ' + args.user_id if args.user_id else ''}:")
    print(f"  Total Cost: ${summary['total_cost']:.4f}")
    print(f"  Total Tokens: {summary['total_tokens']:,}")
    print(f"  Total Calls: {summary['total_calls']:,}")
    print(f"  Average Cost per Call: ${summary['average_cost_per_call']:.4f}")
    
    if summary['model_breakdown']:
        print("\nModel Breakdown:")
        for model, cost in summary['model_breakdown'].items():
            print(f"  {model}: ${cost:.4f}")


def handle_top_users_command(reporter, args):
    """Handle top users command."""
    top_users = reporter.get_top_users_by_cost(args.limit)
    print(f"Top {len(top_users)} Users by Cost:")
    for i, user in enumerate(top_users, 1):
        print(f"{i:2d}. {user['user_id']}: ${user['total_cost']:.4f} "
              f"({user['total_tokens']:,} tokens, {user['total_calls']} calls)")


def handle_top_agents_command(reporter, args):
    """Handle top agents command."""
    top_agents = reporter.get_top_agents_by_cost(args.limit)
    print(f"Top {len(top_agents)} Agents by Cost:")
    for i, agent in enumerate(top_agents, 1):
        print(f"{i:2d}. {agent['agent_name']}: ${agent['total_cost']:.4f} "
              f"({agent['total_tokens']:,} tokens, {agent['total_calls']} calls)")


def handle_model_stats_command(reporter, args):
    """Handle model stats command."""
    model_stats = reporter.get_model_statistics()
    print("Model Usage Statistics:")
    for model, stats in model_stats.items():
        print(f"  {model}:")
        print(f"    Total Cost: ${stats['total_cost']:.4f}")
        print(f"    Total Tokens: {stats['total_tokens']:,}")
        print(f"    Total Calls: {stats['total_calls']:,}")


def handle_export_command(reporter, args):
    """Handle export command."""
    success = reporter.export_data(args.output, args.format)
    if success:
        print(f"Data exported to {args.output} in {args.format.upper()} format")
    else:
        print("Export failed")


def handle_estimate_command(tracker, args):
    """Handle estimate command."""
    estimated_cost = tracker.estimate_cost(args.model, args.input_tokens, args.output_tokens)
    print(f"Estimated cost for {args.model}:")
    print(f"  Input tokens: {args.input_tokens:,}")
    print(f"  Output tokens: {args.output_tokens:,}")
    print(f"  Estimated cost: ${estimated_cost:.4f}")


def handle_metadata_command(tracker, args):
    """Handle metadata command."""
    all_data = tracker.get_all_data()
    records_with_metadata = [
        record for record in all_data 
        if record.get("usage_metadata_json")
    ]
    
    print(f"Usage Metadata Details (showing {min(args.limit, len(records_with_metadata))} records):")
    for i, record in enumerate(records_with_metadata[:args.limit], 1):
        print(f"\n{i}. Record ID: {record['id']}")
        print(f"   User: {record['user_id']}")
        print(f"   Model: {record['model_name']}")
        print(f"   Cost: ${record['cost']:.4f}")
        print(f"   Timestamp: {record['timestamp']}")
        
        # Parse and display metadata
        try:
            metadata = tracker.parse_usage_metadata(record['usage_metadata_json'])
            print(f"   Usage Metadata:")
            print(f"     Input tokens: {metadata.get('input_tokens', 0)}")
            print(f"     Output tokens: {metadata.get('output_tokens', 0)}")
            print(f"     Total tokens: {metadata.get('total_tokens', 0)}")
            
            # Show detailed token info if available
            input_details = metadata.get('input_token_details', {})
            output_details = metadata.get('output_token_details', {})
            if input_details or output_details:
                print(f"     Token Details:")
                if input_details:
                    for key, value in input_details.items():
                        if value > 0:
                            print(f"       Input {key}: {value}")
                if output_details:
                    for key, value in output_details.items():
                        if value > 0:
                            print(f"       Output {key}: {value}")
        except Exception as e:
            print(f"   Error parsing metadata: {e}")


if __name__ == "__main__":
    main()
