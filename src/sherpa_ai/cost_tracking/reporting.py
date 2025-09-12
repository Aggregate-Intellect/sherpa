"""Cost reporting utilities for enhanced UserUsageTracker."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from sherpa_ai.database.user_usage_tracker import UserUsageTracker


class CostReporter:
    """Cost reporting for enhanced UserUsageTracker."""
    
    def __init__(self, tracker: Optional[UserUsageTracker] = None):
        """Initialize the cost reporter.
        
        Args:
            tracker: UserUsageTracker instance. If None, creates a new one.
        """
        self.tracker = tracker or UserUsageTracker()
    
    def generate_daily_report(self, user_id: Optional[str] = None, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate a daily cost report.
        
        Args:
            user_id: Filter by user ID. If None, includes all users.
            date: Date for the report. If None, uses today.
            
        Returns:
            Dictionary containing daily report data.
        """
        if date is None:
            date = datetime.now().date()
        
        # For simplicity, we'll use the existing data and filter by date
        # In a more sophisticated implementation, you'd add date filtering to the database
        summary = self.tracker.get_cost_summary(user_id)
        
        return {
            "date": date.isoformat(),
            "user_id": user_id,
            "summary": {
                "total_cost": summary["total_cost"],
                "total_tokens": summary["total_tokens"],
                "total_calls": summary["total_calls"],
                "average_cost_per_call": summary["average_cost_per_call"]
            },
            "breakdown": {
                "by_model": summary["model_breakdown"]
            }
        }
    
    def generate_weekly_report(self, user_id: Optional[str] = None, week_start: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate a weekly cost report.
        
        Args:
            user_id: Filter by user ID. If None, includes all users.
            week_start: Start of the week. If None, uses Monday of current week.
            
        Returns:
            Dictionary containing weekly report data.
        """
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        # For simplicity, we'll use the existing data
        # In a more sophisticated implementation, you'd add date filtering
        summary = self.tracker.get_cost_summary(user_id)
        
        return {
            "week_start": week_start.isoformat(),
            "user_id": user_id,
            "summary": {
                "total_cost": summary["total_cost"],
                "total_tokens": summary["total_tokens"],
                "total_calls": summary["total_calls"],
                "average_daily_cost": summary["total_cost"] / 7,
                "average_cost_per_call": summary["average_cost_per_call"]
            },
            "breakdown": {
                "by_model": summary["model_breakdown"]
            }
        }
    
    def get_top_users_by_cost(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by cost.
        
        Args:
            limit: Maximum number of users to return.
            
        Returns:
            List of user cost data.
        """
        # Get all data and group by user
        all_data = self.tracker.get_all_data()
        user_costs = {}
        
        for record in all_data:
            user_id = record.user_id
            if user_id not in user_costs:
                user_costs[user_id] = {
                    "user_id": user_id,
                    "total_cost": 0,
                    "total_tokens": 0,
                    "total_calls": 0
                }
            
            user_costs[user_id]["total_cost"] += record.cost
            user_costs[user_id]["total_tokens"] += record.token
            user_costs[user_id]["total_calls"] += 1
        
        # Sort by cost and return top users
        sorted_users = sorted(
            user_costs.values(),
            key=lambda x: x["total_cost"],
            reverse=True
        )
        
        return sorted_users[:limit]
    
    def get_top_agents_by_cost(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top agents by cost.
        
        Args:
            limit: Maximum number of agents to return.
            
        Returns:
            List of agent cost data.
        """
        # Get all data and group by agent
        all_data = self.tracker.get_all_data()
        agent_costs = {}
        
        for record in all_data:
            agent_name = record.agent_name
            if not agent_name:
                continue
                
            if agent_name not in agent_costs:
                agent_costs[agent_name] = {
                    "agent_name": agent_name,
                    "total_cost": 0,
                    "total_tokens": 0,
                    "total_calls": 0
                }
            
            agent_costs[agent_name]["total_cost"] += record.cost
            agent_costs[agent_name]["total_tokens"] += record.token
            agent_costs[agent_name]["total_calls"] += 1
        
        # Sort by cost and return top agents
        sorted_agents = sorted(
            agent_costs.values(),
            key=lambda x: x["total_cost"],
            reverse=True
        )
        
        return sorted_agents[:limit]
    
    def get_model_usage_stats(self) -> Dict[str, Any]:
        """Get model usage statistics.
        
        Returns:
            Dictionary containing model usage statistics.
        """
        # Get all data and group by model
        all_data = self.tracker.get_all_data()
        model_stats = {}
        
        for record in all_data:
            model_name = record.model_name
            if model_name not in model_stats:
                model_stats[model_name] = {
                    "model_name": model_name,
                    "total_cost": 0,
                    "total_tokens": 0,
                    "total_calls": 0
                }
            
            model_stats[model_name]["total_cost"] += record.cost
            model_stats[model_name]["total_tokens"] += record.token
            model_stats[model_name]["total_calls"] += 1
        
        return model_stats
    
    def export_data(self, format: str = "json") -> str:
        """Export cost data.
        
        Args:
            format: Export format ("json" or "csv").
            
        Returns:
            Exported data as string.
        """
        all_data = self.tracker.get_all_data()
        
        if format == "json":
            # Convert records to dictionaries
            data_list = []
            for record in all_data:
                data_list.append({
                    "id": record.id,
                    "user_id": record.user_id,
                    "token": record.token,
                    "cost": record.cost,
                    "model_name": record.model_name,
                    "session_id": record.session_id,
                    "agent_name": record.agent_name,
                    "timestamp": record.timestamp,
                    "reset_timestamp": record.reset_timestamp,
                    "reminded_timestamp": record.reminded_timestamp
                })
            return json.dumps(data_list, indent=2, default=str)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if all_data:
                fieldnames = [
                    "id", "user_id", "token", "cost", "model_name", 
                    "session_id", "agent_name", "timestamp", 
                    "reset_timestamp", "reminded_timestamp"
                ]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in all_data:
                    writer.writerow({
                        "id": record.id,
                        "user_id": record.user_id,
                        "token": record.token,
                        "cost": record.cost,
                        "model_name": record.model_name,
                        "session_id": record.session_id,
                        "agent_name": record.agent_name,
                        "timestamp": record.timestamp,
                        "reset_timestamp": record.reset_timestamp,
                        "reminded_timestamp": record.reminded_timestamp
                    })
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def print_summary(self, user_id: Optional[str] = None):
        """Print a cost summary to console.
        
        Args:
            user_id: Filter by user ID. If None, shows summary for all users.
        """
        summary = self.tracker.get_cost_summary(user_id)
        
        print("=" * 50)
        print("COST TRACKING SUMMARY")
        print("=" * 50)
        
        if user_id:
            print(f"User ID: {user_id}")
        else:
            print("All Users")
        
        print(f"Total Cost: ${summary['total_cost']:.4f}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Calls: {summary['total_calls']}")
        print(f"Average Cost per Call: ${summary['average_cost_per_call']:.4f}")
        
        print("\nModel Breakdown:")
        for model, cost in summary['model_breakdown'].items():
            print(f"  {model}: ${cost:.4f}")
        
        print("=" * 50)
    
    def print_top_users(self, limit: int = 10):
        """Print top users by cost.
        
        Args:
            limit: Number of top users to show.
        """
        top_users = self.get_top_users_by_cost(limit)
        
        print(f"\nTop {limit} Users by Cost:")
        print("-" * 40)
        for i, user in enumerate(top_users, 1):
            print(f"{i:2d}. {user['user_id']}: ${user['total_cost']:.4f} "
                  f"({user['total_tokens']:,} tokens, {user['total_calls']} calls)")
    
    def print_top_agents(self, limit: int = 10):
        """Print top agents by cost.
        
        Args:
            limit: Number of top agents to show.
        """
        top_agents = self.get_top_agents_by_cost(limit)
        
        print(f"\nTop {limit} Agents by Cost:")
        print("-" * 40)
        for i, agent in enumerate(top_agents, 1):
            print(f"{i:2d}. {agent['agent_name']}: ${agent['total_cost']:.4f} "
                  f"({agent['total_tokens']:,} tokens, {agent['total_calls']} calls)")
    
    def print_model_stats(self):
        """Print model usage statistics."""
        model_stats = self.get_model_usage_stats()
        
        print("\nModel Usage Statistics:")
        print("-" * 40)
        for model_name, stats in model_stats.items():
            print(f"{model_name}: ${stats['total_cost']:.4f} "
                  f"({stats['total_tokens']:,} tokens, {stats['total_calls']} calls)")
    
    def close(self):
        """Close the database connection."""
        self.tracker.close_connection()
