"""Cost reporting utilities for enhanced UserUsageTracker."""

from typing import Dict, List, Optional, Any
import json

from sherpa_ai.database.user_usage_tracker import UserUsageTracker, UsageTracker


class CostReporter:
    """Cost reporting for enhanced UserUsageTracker."""
    
    def __init__(self, tracker: Optional[UserUsageTracker] = None):
        """Initialize the cost reporter."""
        self.tracker = tracker or UserUsageTracker()
    
    def get_tokens_from_usage_metadata(self, usage_metadata: Dict[str, Any]) -> Dict[str, int]:
        """Extract token counts from usage metadata."""
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)
        total_tokens = usage_metadata.get("total_tokens", 0)
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }
    
    def get_token_details_from_usage_metadata(self, usage_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed token information from usage metadata."""
        input_details = usage_metadata.get("input_token_details", {})
        output_details = usage_metadata.get("output_token_details", {})
        return {
            "reasoning_tokens": output_details.get("reasoning", 0),
            "cache_creation": input_details.get("cache_creation", 0),
            "cache_read": input_details.get("cache_read", 0),
            "audio_tokens": input_details.get("audio", 0) + output_details.get("audio", 0)
        }
    
    def get_usage_metadata_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed usage statistics from usage metadata."""
        if user_id:
            data = self.tracker.session.query(UsageTracker).filter_by(user_id=user_id).all()
        else:
            data = self.tracker.session.query(UsageTracker).all()
        
        if not data:
            return {
                "total_records": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "model_breakdown": {},
                "token_details": {}
            }
        
        total_cost = sum(item.cost for item in data)
        total_tokens = 0
        model_breakdown = {}
        token_details = {
            "reasoning_tokens": 0,
            "cache_creation": 0,
            "cache_read": 0,
            "audio_tokens": 0
        }
        
        for record in data:
            # Extract tokens from usage_metadata_json
            if record.usage_metadata_json:
                try:
                    usage_metadata = json.loads(record.usage_metadata_json)
                    token_info = self.get_tokens_from_usage_metadata(usage_metadata)
                    total_tokens += token_info.get("total_tokens", 0)
                    
                    # Extract detailed token info
                    details = self.get_token_details_from_usage_metadata(usage_metadata)
                    for key, value in details.items():
                        token_details[key] += value
                except (json.JSONDecodeError, KeyError):
                    continue
            
            # Model breakdown
            model = record.model_name or "unknown"
            model_breakdown[model] = model_breakdown.get(model, 0) + record.cost
        
        return {
            "total_records": len(data),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "model_breakdown": model_breakdown,
            "token_details": token_details
        }
    
    def get_top_users_by_cost(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by cost."""
        data = self.tracker.session.query(UsageTracker).all()
        
        # Group by user_id
        user_costs = {}
        for record in data:
            user_id = record.user_id
            if user_id not in user_costs:
                user_costs[user_id] = {
                    "user_id": user_id,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_calls": 0,
                    "models_used": set()
                }
            
            user_costs[user_id]["total_cost"] += record.cost
            user_costs[user_id]["total_calls"] += 1
            user_costs[user_id]["models_used"].add(record.model_name or "unknown")
            
            # Extract tokens from usage_metadata_json
            if record.usage_metadata_json:
                try:
                    usage_metadata = json.loads(record.usage_metadata_json)
                    token_info = self.get_tokens_from_usage_metadata(usage_metadata)
                    user_costs[user_id]["total_tokens"] += token_info.get("total_tokens", 0)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Convert sets to lists and sort by cost
        result = []
        for user_data in user_costs.values():
            user_data["models_used"] = list(user_data["models_used"])
            result.append(user_data)
        
        return sorted(result, key=lambda x: x["total_cost"], reverse=True)[:limit]
    
    def get_top_agents_by_cost(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top agents by cost."""
        data = self.tracker.session.query(UsageTracker).all()
        
        # Group by agent_name
        agent_costs = {}
        for record in data:
            agent_name = record.agent_name or "unknown"
            if agent_name not in agent_costs:
                agent_costs[agent_name] = {
                    "agent_name": agent_name,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_calls": 0
                }
            
            agent_costs[agent_name]["total_cost"] += record.cost
            agent_costs[agent_name]["total_calls"] += 1
            
            # Extract tokens from usage_metadata_json
            if record.usage_metadata_json:
                try:
                    usage_metadata = json.loads(record.usage_metadata_json)
                    token_info = self.get_tokens_from_usage_metadata(usage_metadata)
                    agent_costs[agent_name]["total_tokens"] += token_info.get("total_tokens", 0)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Sort by cost
        result = list(agent_costs.values())
        return sorted(result, key=lambda x: x["total_cost"], reverse=True)[:limit]
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get model usage statistics."""
        data = self.tracker.session.query(UsageTracker).all()
        
        model_stats = {}
        for record in data:
            model_name = record.model_name or "unknown"
            if model_name not in model_stats:
                model_stats[model_name] = {
                    "model_name": model_name,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_calls": 0
                }
            
            model_stats[model_name]["total_cost"] += record.cost
            model_stats[model_name]["total_calls"] += 1
            
            # Extract tokens from usage_metadata_json
            if record.usage_metadata_json:
                try:
                    usage_metadata = json.loads(record.usage_metadata_json)
                    token_info = self.get_tokens_from_usage_metadata(usage_metadata)
                    model_stats[model_name]["total_tokens"] += token_info.get("total_tokens", 0)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return model_stats
    
    def export_data(self, output_path: str, format: str = "json") -> bool:
        """Export cost data to file."""
        try:
            data = self.tracker.get_all_data()
            
            if format == "json":
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif format == "csv":
                import csv
                if data:
                    with open(output_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
