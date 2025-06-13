"""
Different methods for reranking the results of a search query.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

import numpy as np
from nltk import tokenize
from numpy.typing import ArrayLike
from pydantic import BaseModel
from langchain_core.language_models.base import BaseLanguageModel


SEARCH_SUMMARY_DESCRIPTION = """Question：{question} 
Relevant Answer:
{answer}


Review and extract the most relevant sentences from relevant answer. 
Need to follows rules:
1. The output sentences should only picked from original relevant answer.
2. Return 'not relevant.' if relevant answer is not relevant to the question asked."""

SEARCH_SUMMARY_DESCRIPTION_SENT = """Question：{question} 
Potential relevant sentences to the question:
{answer}
Review answer and return only bullet point number which are related to the question, separated by comma. E,g. 2,3,4
"""


class BaseRefinement(ABC, BaseModel):
    """Abstract base class for refinement actions.
    
    This class provides a base implementation for refinement actions that can be
    used to refine search results or extract relevant information from documents.
    
    Attributes:
        llm (Any): Language model used for refinement.
        description (str): Description of the refinement action.
        k (int): Number of results to return.
    
    Example:
        >>> from sherpa_ai.actions.utils import RefinementByQuery
        >>> refinement = RefinementByQuery(llm=my_llm)
        >>> results = refinement.refinement(documents, query)
    """
    @abstractmethod
    def refinement(self, documents: list[str], **kwargs) -> str:
        pass


class RefinementByQuery(BaseRefinement):
    """Refinement action that refines search results based on a query.
    
    This class provides a refinement action that refines search results based on a query.
    It uses an LLM to refine the search results and return the most relevant sentences.
    
    Attributes:
        llm (Any): Language model used for refinement.
        description (str): Description of the refinement action.
        k (int): Number of results to return.
    
    Example:
        >>> from sherpa_ai.actions.utils import RefinementByQuery
        >>> refinement = RefinementByQuery(llm=my_llm)
        >>> results = refinement.refinement(documents, query)
    """
    llm: Optional[BaseLanguageModel] = None 
    description: str = SEARCH_SUMMARY_DESCRIPTION
    k: int = 3

    def refinement(self, documents: list[str], query: str) -> list[str]:
        """Refine the search results based on the query.

        Args:
            documents (list[str]): The documents to refine.
            query (str): The query to refine the documents.
        
        Returns:
            list[str]: The refined search results.

        Raises:
            SherpaActionExecutionException: If the action fails to execute.
        """
        refined_result = []
        for doc in documents:
            res = self.llm.invoke(
                self.description.format(question=query, answer=doc, k=self.k)
            )
            if res.lower() != "not relevant.":
                refined_result.append(res)
        return refined_result


class RefinementBySentence(BaseRefinement):
    """Refinement action that refines search results based on a sentence.
    
    This class provides a refinement action that refines search results based on a sentence.
    It uses an LLM to refine the search results and return the most relevant sentences.
    
    Attributes:
        llm (Any): Language model used for refinement.
        description (str): Description of the refinement action.
        k (int): Number of results to return.
    
    Example:
        >>> from sherpa_ai.actions.utils import RefinementBySentence
        >>> refinement = RefinementBySentence(llm=my_llm)
        >>> results = refinement.refinement(documents, query)
    """
    llm: Optional[BaseLanguageModel] = None 
    description: str = SEARCH_SUMMARY_DESCRIPTION_SENT

    def refinement(self, documents: list[str], query: str) -> list[str]:
        """Refine the search results based on the sentence.

        Args:
            documents (list[str]): The documents to refine.
            query (str): The query to refine the documents.
        
        Returns:
            list[str]: The refined search results.

        Raises:
            SherpaActionExecutionException: If the action fails to execute.
        """
        refined_result = []
        for doc in documents:
            ans_value = tokenize.sent_tokenize(doc)
            ans_key = range(0, len(ans_value))
            ans_bullet = dict(zip(ans_key, ans_value))
            answer_bullet = ""
            for key, value in ans_bullet.items():
                answer_bullet += str(key) + ". " + value + "\n"
            res = self.llm.invoke(
                self.description.format(question=query, answer=answer_bullet)
            )
            list_res = res.split(",")
            list_check = [i.isdigit() for i in list_res]
            if all(list_check):
                refined_res = " ".join([ans_bullet[int(i)] for i in list_res])
                refined_result.append(refined_res)
        return refined_result
