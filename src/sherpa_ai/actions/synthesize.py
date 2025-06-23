from typing import Any, Optional

from langchain_core.language_models.base import BaseLanguageModel 
from loguru import logger 

from sherpa_ai.actions.base import BaseAction


class SynthesizeOutput(BaseAction):
    """An action for synthesizing information into a coherent response.
    
    This class provides functionality to generate responses by combining task
    requirements, context, and conversation history, with optional citation support.
    
    This class inherits from :class:`BaseAction` and provides methods to:
      - Generate synthesized responses based on multiple inputs
      - Format responses with or without citations
      - Process and structure output using templates
    
    Attributes:
        role_description (str): Description of the role context for response generation.
        llm (Any): Language model used for generating responses.
        description (str): Custom description template for response generation.
        add_citation (bool): Whether to include citations in the response.
        name (str): Name of the action, set to "SynthesizeOutput".
        args (dict): Arguments required by the action.
        usage (str): Description of the action's usage.
    
    Example:
        >>> synthesizer = SynthesizeOutput(
        ...     role_description="AI assistant",
        ...     llm=my_llm,
        ...     add_citation=True
        ... )
        >>> response = synthesizer.execute(
        ...     task="Summarize the benefits of exercise",
        ...     context="Exercise improves cardiovascular health and mental well-being",
        ...     history="User: Tell me about exercise benefits"
        ... )
        >>> print(response)
        Exercise provides numerous health benefits, including improved cardiovascular health and mental well-being [1].
    """
    
    role_description: str
    llm: Optional[BaseLanguageModel] = None
    description: str = None
    add_citation: bool = False

    # Override the name and args from BaseAction
    name: str = "SynthesizeOutput"
    args: dict = {"task": "string", "context": "string", "history": "string"}
    usage: str = "Answer the question using conversation history with the user"

    def __init__(self, **kwargs):
        """Initialize a SynthesizeOutput action with the provided parameters.
        
        Args:
            **kwargs: Keyword arguments passed to the parent class.
        """
        super().__init__(**kwargs)
         

    def execute(self, task: str, context: str, history: str) -> str:
        """Generate a synthesized response based on the provided inputs.
        
        This method combines task requirements, context, and conversation history
        to generate a coherent response, with optional citation support.
        
        Args:
            task (str): The task or question to address.
            context (str): Relevant context information for the response.
            history (str): Conversation history for context.
            
        Returns:
            str: The generated response text.
        """
        if self.description:
            prompt =self.description.format(
                task=task,
                context=context,
                history=history,
                role_description=self.role_description,
            )
        else:
            variables = {
                "role_description": self.role_description,
                "task": task,
                "context": context,
                "history": history,
            }
            prompt = self.prompt_template.format_prompt(
                prompt_parent_id="synthesize_prompts",
                prompt_id="SYNTHESIZE_DESCRIPTION_CITATION" if self.add_citation else "SYNTHESIZE_DESCRIPTION",
                version="1.0",
                variables=variables
            )

        logger.debug("Prompt: {}", prompt)
        prompt_str = self.prompt_template.format_prompt(
            prompt_parent_id="synthesize_prompts",
            prompt_id="SYNTHESIZE_DESCRIPTION",
            version="1.0",
            variables=variables
        )
        result = self.llm.invoke(prompt_str)
        result_text = result.content if hasattr(result, 'content') else str(result)
        return result_text
