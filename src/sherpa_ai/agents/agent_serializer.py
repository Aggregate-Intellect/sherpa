"""Agent serialization and deserialization module for Sherpa AI.

This module provides comprehensive serialization and deserialization capabilities
for agents, including handling of complex objects like LLMs, policies, and actions.
"""

import json
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.shared_memory import SharedMemory


class SerializationContext(BaseModel):
    """Context for agent serialization/deserialization.
    
    Attributes:
        include_llm (bool): Whether to include LLM in serialization.
        include_actions (bool): Whether to include actions in serialization.
        include_policy (bool): Whether to include policy in serialization.
        compression_level (int): Compression level for binary data.
        custom_serializers (Dict[str, Any]): Custom serializers for specific types.
    """
    
    include_llm: bool = Field(default=True)
    include_actions: bool = Field(default=True)
    include_policy: bool = Field(default=True)
    compression_level: int = Field(default=1)
    custom_serializers: Dict[str, Any] = Field(default_factory=dict)


class AgentSerializer(ABC):
    """Abstract base class for agent serializers."""
    
    @abstractmethod
    def serialize(self, agent: BaseAgent, context: SerializationContext) -> Dict[str, Any]:
        """Serialize an agent to a dictionary.
        
        Args:
            agent (BaseAgent): The agent to serialize.
            context (SerializationContext): Serialization context.
            
        Returns:
            Dict[str, Any]: Serialized agent data.
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: Dict[str, Any], context: SerializationContext) -> Optional[BaseAgent]:
        """Deserialize an agent from a dictionary.
        
        Args:
            data (Dict[str, Any]): Serialized agent data.
            context (SerializationContext): Deserialization context.
            
        Returns:
            Optional[BaseAgent]: Deserialized agent or None if failed.
        """
        pass


class DefaultAgentSerializer(AgentSerializer):
    """Default implementation of agent serializer.
    
    This serializer handles basic agent serialization and deserialization,
    with support for common agent types and configurations.
    """
    
    def __init__(self):
        """Initialize the default serializer."""
        self.agent_registry = self._build_agent_registry()
    
    def _build_agent_registry(self) -> Dict[str, Type[BaseAgent]]:
        """Build registry of available agent types.
        
        Returns:
            Dict[str, Type[BaseAgent]]: Mapping of agent type names to classes.
        """
        registry = {}
        
        try:
            # Import agent types dynamically to avoid circular imports
            from sherpa_ai.agents.qa_agent import QAAgent
            from sherpa_ai.agents.ml_engineer import MLEngineer
            from sherpa_ai.agents.critic import Critic
            from sherpa_ai.agents.user import UserAgent
            
            registry.update({
                "QAAgent": QAAgent,
                "MLEngineer": MLEngineer,
                "Critic": Critic,
                "UserAgent": UserAgent,
            })
            
        except ImportError as e:
            logger.warning(f"Could not import some agent types: {e}")
        
        return registry
    
    def serialize(self, agent: BaseAgent, context: SerializationContext) -> Dict[str, Any]:
        """Serialize an agent to a dictionary.
        
        Args:
            agent (BaseAgent): The agent to serialize.
            context (SerializationContext): Serialization context.
            
        Returns:
            Dict[str, Any]: Serialized agent data.
        """
        try:
            # Basic agent data
            data = {
                "agent_type": agent.__class__.__name__,
                "name": agent.name,
                "description": agent.description,
                "num_runs": getattr(agent, 'num_runs', 1),
                "validation_steps": getattr(agent, 'validation_steps', 1),
                "global_regen_max": getattr(agent, 'global_regen_max', 12),
                "feedback_agent_name": getattr(agent, 'feedback_agent_name', 'critic'),
            }
            
            # Serialize belief state
            if hasattr(agent, 'belief') and agent.belief:
                data["belief"] = self._serialize_belief(agent.belief)
            
            # Serialize shared memory
            if hasattr(agent, 'shared_memory') and agent.shared_memory:
                data["shared_memory"] = self._serialize_shared_memory(agent.shared_memory)
            
            # Serialize LLM (if requested and available)
            if context.include_llm and hasattr(agent, 'llm') and agent.llm:
                data["llm"] = self._serialize_llm(agent.llm)
            
            # Serialize actions (if requested and available)
            if context.include_actions and hasattr(agent, 'actions') and agent.actions:
                data["actions"] = self._serialize_actions(agent.actions)
            
            # Serialize policy (if requested and available)
            if context.include_policy and hasattr(agent, 'policy') and agent.policy:
                data["policy"] = self._serialize_policy(agent.policy)
            
            # Serialize validations
            if hasattr(agent, 'validations') and agent.validations:
                data["validations"] = self._serialize_validations(agent.validations)
            
            # Serialize prompt template
            if hasattr(agent, 'prompt_template') and agent.prompt_template:
                data["prompt_template"] = self._serialize_prompt_template(agent.prompt_template)
            
            # Add custom serializations
            for key, serializer in context.custom_serializers.items():
                if hasattr(agent, key):
                    data[key] = serializer(getattr(agent, key))
            
            # Ensure all data is JSON-serializable
            return self._ensure_json_serializable(data)
            
        except Exception as e:
            logger.error(f"Failed to serialize agent {agent.name}: {e}")
            raise
    
    def deserialize(self, data: Dict[str, Any], context: SerializationContext) -> Optional[BaseAgent]:
        """Deserialize an agent from a dictionary.
        
        Args:
            data (Dict[str, Any]): Serialized agent data.
            context (SerializationContext): Deserialization context.
            
        Returns:
            Optional[BaseAgent]: Deserialized agent or None if failed.
        """
        try:
            agent_type = data.get("agent_type")
            if not agent_type or agent_type not in self.agent_registry:
                logger.error(f"Unknown agent type: {agent_type}")
                return None
            
            agent_class = self.agent_registry[agent_type]
            
            # Prepare agent initialization parameters
            init_params = {
                "name": data.get("name", "Unnamed Agent"),
                "description": data.get("description", ""),
            }
            
            # Deserialize and add optional parameters
            if "num_runs" in data:
                init_params["num_runs"] = data["num_runs"]
            if "validation_steps" in data:
                init_params["validation_steps"] = data["validation_steps"]
            if "global_regen_max" in data:
                init_params["global_regen_max"] = data["global_regen_max"]
            if "feedback_agent_name" in data:
                init_params["feedback_agent_name"] = data["feedback_agent_name"]
            
            # Create agent instance
            agent = agent_class(**init_params)
            
            # Deserialize belief state
            if "belief" in data:
                agent.belief = self._deserialize_belief(data["belief"])
            
            # Deserialize shared memory
            if "shared_memory" in data:
                agent.shared_memory = self._deserialize_shared_memory(data["shared_memory"])
            
            # Deserialize LLM
            if context.include_llm and "llm" in data:
                agent.llm = self._deserialize_llm(data["llm"])
            
            # Deserialize actions
            if context.include_actions and "actions" in data:
                agent.actions = self._deserialize_actions(data["actions"])
            
            # Deserialize policy
            if context.include_policy and "policy" in data:
                agent.policy = self._deserialize_policy(data["policy"])
            
            # Deserialize validations
            if "validations" in data:
                agent.validations = self._deserialize_validations(data["validations"])
            
            # Deserialize prompt template
            if "prompt_template" in data:
                agent.prompt_template = self._deserialize_prompt_template(data["prompt_template"])
            
            # Apply custom deserializations
            for key, deserializer in context.custom_serializers.items():
                if key in data:
                    setattr(agent, key, deserializer(data[key]))
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to deserialize agent: {e}")
            return None
    
    def _serialize_belief(self, belief: Belief) -> Dict[str, Any]:
        """Serialize a belief object.
        
        Args:
            belief (Belief): The belief to serialize.
            
        Returns:
            Dict[str, Any]: Serialized belief data.
        """
        try:
            return belief.model_dump()
        except Exception as e:
            logger.warning(f"Failed to serialize belief: {e}")
            return {}
    
    def _deserialize_belief(self, data: Dict[str, Any]) -> Optional[Belief]:
        """Deserialize a belief object.
        
        Args:
            data (Dict[str, Any]): Serialized belief data.
            
        Returns:
            Optional[Belief]: Deserialized belief or None if failed.
        """
        try:
            return Belief.model_validate(data)
        except ValidationError as e:
            logger.warning(f"Failed to deserialize belief: {e}")
            return None
    
    def _serialize_shared_memory(self, shared_memory: SharedMemory) -> Dict[str, Any]:
        """Serialize a shared memory object.
        
        Args:
            shared_memory (SharedMemory): The shared memory to serialize.
            
        Returns:
            Dict[str, Any]: Serialized shared memory data.
        """
        try:
            return {
                "objective": shared_memory.objective,
                "events": [event.model_dump() for event in shared_memory.events]
            }
        except Exception as e:
            logger.warning(f"Failed to serialize shared memory: {e}")
            return {"objective": "", "events": []}
    
    def _deserialize_shared_memory(self, data: Dict[str, Any]) -> Optional[SharedMemory]:
        """Deserialize a shared memory object.
        
        Args:
            data (Dict[str, Any]): Serialized shared memory data.
            
        Returns:
            Optional[SharedMemory]: Deserialized shared memory or None if failed.
        """
        try:
            from sherpa_ai.events import Event, build_event
            
            shared_memory = SharedMemory(data.get("objective", ""))
            
            # Reconstruct events
            for event_data in data.get("events", []):
                try:
                    event = build_event(
                        event_data.get("event_type", ""),
                        event_data.get("name", ""),
                        event_data.get("sender", ""),
                        **event_data.get("args", {})
                    )
                    shared_memory.events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to deserialize event: {e}")
            
            return shared_memory
            
        except Exception as e:
            logger.warning(f"Failed to deserialize shared memory: {e}")
            return None
    
    def _serialize_llm(self, llm: Any) -> Dict[str, Any]:
        """Serialize an LLM object.
        
        Args:
            llm (Any): The LLM to serialize.
            
        Returns:
            Dict[str, Any]: Serialized LLM data.
        """
        try:
            # For now, we'll store basic LLM configuration
            # In a real implementation, you'd need to handle different LLM types
            return {
                "type": llm.__class__.__name__,
                "config": getattr(llm, 'model_dump', lambda: {})(),
            }
        except Exception as e:
            logger.warning(f"Failed to serialize LLM: {e}")
            return {"type": "Unknown", "config": {}}
    
    def _deserialize_llm(self, data: Dict[str, Any]) -> Optional[Any]:
        """Deserialize an LLM object.
        
        Args:
            data (Dict[str, Any]): Serialized LLM data.
            
        Returns:
            Optional[Any]: Deserialized LLM or None if failed.
        """
        try:
            # This is a simplified implementation
            # In practice, you'd need to handle different LLM types and their specific configurations
            logger.warning("LLM deserialization not fully implemented")
            return None
        except Exception as e:
            logger.warning(f"Failed to deserialize LLM: {e}")
            return None
    
    def _serialize_actions(self, actions: List[Any]) -> List[Dict[str, Any]]:
        """Serialize a list of actions.
        
        Args:
            actions (List[Any]): The actions to serialize.
            
        Returns:
            List[Dict[str, Any]]: Serialized actions data.
        """
        try:
            serialized_actions = []
            for action in actions:
                if hasattr(action, 'model_dump'):
                    serialized_actions.append(action.model_dump())
                else:
                    # Fallback for actions without model_dump
                    serialized_actions.append({
                        "type": action.__class__.__name__,
                        "name": getattr(action, 'name', ''),
                        "usage": getattr(action, 'usage', ''),
                    })
            return serialized_actions
        except Exception as e:
            logger.warning(f"Failed to serialize actions: {e}")
            return []
    
    def _deserialize_actions(self, data: List[Dict[str, Any]]) -> List[Any]:
        """Deserialize a list of actions.
        
        Args:
            data (List[Dict[str, Any]]): Serialized actions data.
            
        Returns:
            List[Any]: Deserialized actions.
        """
        try:
            # This is a simplified implementation
            # In practice, you'd need to handle different action types and their specific configurations
            logger.warning("Action deserialization not fully implemented")
            return []
        except Exception as e:
            logger.warning(f"Failed to deserialize actions: {e}")
            return []
    
    def _serialize_policy(self, policy: Any) -> Dict[str, Any]:
        """Serialize a policy object.
        
        Args:
            policy (Any): The policy to serialize.
            
        Returns:
            Dict[str, Any]: Serialized policy data.
        """
        try:
            if hasattr(policy, 'model_dump'):
                return policy.model_dump()
            else:
                return {
                    "type": policy.__class__.__name__,
                    "config": getattr(policy, '__dict__', {}),
                }
        except Exception as e:
            logger.warning(f"Failed to serialize policy: {e}")
            return {"type": "Unknown", "config": {}}
    
    def _deserialize_policy(self, data: Dict[str, Any]) -> Optional[Any]:
        """Deserialize a policy object.
        
        Args:
            data (Dict[str, Any]): Serialized policy data.
            
        Returns:
            Optional[Any]: Deserialized policy or None if failed.
        """
        try:
            # This is a simplified implementation
            # In practice, you'd need to handle different policy types and their specific configurations
            logger.warning("Policy deserialization not fully implemented")
            return None
        except Exception as e:
            logger.warning(f"Failed to deserialize policy: {e}")
            return None
    
    def _serialize_validations(self, validations: List[Any]) -> List[Dict[str, Any]]:
        """Serialize a list of validations.
        
        Args:
            validations (List[Any]): The validations to serialize.
            
        Returns:
            List[Dict[str, Any]]: Serialized validations data.
        """
        try:
            serialized_validations = []
            for validation in validations:
                if hasattr(validation, 'model_dump'):
                    serialized_validations.append(validation.model_dump())
                else:
                    serialized_validations.append({
                        "type": validation.__class__.__name__,
                        "config": getattr(validation, '__dict__', {}),
                    })
            return serialized_validations
        except Exception as e:
            logger.warning(f"Failed to serialize validations: {e}")
            return []
    
    def _deserialize_validations(self, data: List[Dict[str, Any]]) -> List[Any]:
        """Deserialize a list of validations.
        
        Args:
            data (List[Dict[str, Any]]): Serialized validations data.
            
        Returns:
            List[Any]: Deserialized validations.
        """
        try:
            # This is a simplified implementation
            # In practice, you'd need to handle different validation types and their specific configurations
            logger.warning("Validation deserialization not fully implemented")
            return []
        except Exception as e:
            logger.warning(f"Failed to deserialize validations: {e}")
            return []
    
    def _serialize_prompt_template(self, prompt_template: Any) -> Dict[str, Any]:
        """Serialize a prompt template object.
        
        Args:
            prompt_template (Any): The prompt template to serialize.
            
        Returns:
            Dict[str, Any]: Serialized prompt template data.
        """
        try:
            if prompt_template is None:
                return {"type": "NoneType", "config": {}}
            
            if hasattr(prompt_template, 'model_dump'):
                return prompt_template.model_dump()
            elif hasattr(prompt_template, 'template'):
                # Handle PromptTemplate objects
                return {
                    "type": prompt_template.__class__.__name__,
                    "template": getattr(prompt_template, 'template', ''),
                    "config": getattr(prompt_template, '__dict__', {}),
                }
            else:
                return {
                    "type": prompt_template.__class__.__name__,
                    "config": getattr(prompt_template, '__dict__', {}),
                }
        except Exception as e:
            logger.warning(f"Failed to serialize prompt template: {e}")
            return {"type": "Unknown", "config": {}}
    
    def _deserialize_prompt_template(self, data: Dict[str, Any]) -> Optional[Any]:
        """Deserialize a prompt template object.
        
        Args:
            data (Dict[str, Any]): Serialized prompt template data.
            
        Returns:
            Optional[Any]: Deserialized prompt template or None if failed.
        """
        try:
            # This is a simplified implementation
            # In practice, you'd need to handle different prompt template types and their specific configurations
            logger.warning("Prompt template deserialization not fully implemented")
            return None
        except Exception as e:
            logger.warning(f"Failed to deserialize prompt template: {e}")
            return None
    
    def _ensure_json_serializable(self, data: Any) -> Any:
        """Ensure data is JSON-serializable by converting non-serializable objects.
        
        Args:
            data (Any): Data to make JSON-serializable.
            
        Returns:
            Any: JSON-serializable data.
        """
        try:
            # Test if data is already JSON-serializable
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            # Convert non-serializable objects
            if isinstance(data, dict):
                return {k: self._ensure_json_serializable(v) for k, v in data.items()}
            elif isinstance(data, (list, tuple)):
                return [self._ensure_json_serializable(item) for item in data]
            elif hasattr(data, '__dict__'):
                # Convert objects to dictionaries
                return {k: self._ensure_json_serializable(v) for k, v in data.__dict__.items()}
            else:
                # Convert to string representation
                return str(data)


class AgentSerializationManager:
    """Manager for agent serialization and deserialization.
    
    This class provides a centralized interface for serializing and deserializing
    agents with different serializers and contexts.
    """
    
    def __init__(self):
        """Initialize the serialization manager."""
        self.serializers: Dict[str, AgentSerializer] = {
            "default": DefaultAgentSerializer(),
        }
        self.default_context = SerializationContext()
    
    def register_serializer(self, name: str, serializer: AgentSerializer):
        """Register a custom serializer.
        
        Args:
            name (str): Name of the serializer.
            serializer (AgentSerializer): The serializer to register.
            
        Example:
            >>> manager = AgentSerializationManager()
            >>> manager.register_serializer("custom", MyCustomSerializer())
        """
        self.serializers[name] = serializer
        logger.info(f"Registered serializer: {name}")
    
    def serialize_agent(self, agent: BaseAgent, serializer_name: str = "default", 
                       context: Optional[SerializationContext] = None) -> Dict[str, Any]:
        """Serialize an agent using the specified serializer.
        
        Args:
            agent (BaseAgent): The agent to serialize.
            serializer_name (str): Name of the serializer to use.
            context (Optional[SerializationContext]): Serialization context.
            
        Returns:
            Dict[str, Any]: Serialized agent data.
            
        Raises:
            ValueError: If serializer is not found.
            
        Example:
            >>> manager = AgentSerializationManager()
            >>> data = manager.serialize_agent(agent, "default")
        """
        if serializer_name not in self.serializers:
            raise ValueError(f"Serializer '{serializer_name}' not found")
        
        serializer = self.serializers[serializer_name]
        context = context or self.default_context
        
        return serializer.serialize(agent, context)
    
    def deserialize_agent(self, data: Dict[str, Any], serializer_name: str = "default",
                         context: Optional[SerializationContext] = None) -> Optional[BaseAgent]:
        """Deserialize an agent using the specified serializer.
        
        Args:
            data (Dict[str, Any]): Serialized agent data.
            serializer_name (str): Name of the serializer to use.
            context (Optional[SerializationContext]): Deserialization context.
            
        Returns:
            Optional[BaseAgent]: Deserialized agent or None if failed.
            
        Raises:
            ValueError: If serializer is not found.
            
        Example:
            >>> manager = AgentSerializationManager()
            >>> agent = manager.deserialize_agent(data, "default")
        """
        if serializer_name not in self.serializers:
            raise ValueError(f"Serializer '{serializer_name}' not found")
        
        serializer = self.serializers[serializer_name]
        context = context or self.default_context
        
        return serializer.deserialize(data, context)
    
    def get_available_serializers(self) -> List[str]:
        """Get list of available serializers.
        
        Returns:
            List[str]: List of serializer names.
            
        Example:
            >>> manager = AgentSerializationManager()
            >>> serializers = manager.get_available_serializers()
            >>> print(serializers)
            ['default']
        """
        return list(self.serializers.keys())
