"""Citation validation and addition module for Sherpa AI.

This module provides functionality for validating and adding citations to text.
It defines the CitationValidation class which analyzes text against source
materials and adds appropriate citations using various similarity metrics.
"""

import nltk
from loguru import logger
from nltk.tokenize import sent_tokenize, word_tokenize

from sherpa_ai.actions.base import ActionResource, BaseRetrievalAction
from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.validation_result import ValidationResult

# download the punkt tokenizer. This is necessary for the sent_tokenize in NLTK.
# The download will only happen once and the result will be cached.
nltk.download("punkt_tab")


class CitationValidation(BaseOutputProcessor):
    """Validator and citation adder for text content.

    This class analyzes text against source materials to validate content and
    add appropriate citations. It uses multiple similarity metrics to determine
    when citations are needed and which sources to cite.

    Attributes:
        sequence_threshold (float): Minimum ratio of common subsequence length
            to text length for citation. Default is 0.7.
        jaccard_threshold (float): Minimum Jaccard similarity for citation.
            Default is 0.7.
        token_overlap (float): Minimum token overlap ratio for citation.
            Default is 0.7.

    Example:
        >>> validator = CitationValidation(sequence_threshold=0.8)
        >>> belief = Belief()  # Contains source about "Python is great"
        >>> result = validator.process_output("Python is great!", belief)
        >>> print("[1]" in result.result)  # Has citation
        True
    """

    def __init__(
        self, sequence_threshold=0.7, jaccard_threshold=0.7, token_overlap=0.7
    ):
        """Initialize a new CitationValidation instance.

        Args:
            sequence_threshold (float): Subsequence length ratio threshold.
            jaccard_threshold (float): Jaccard similarity threshold.
            token_overlap (float): Token overlap ratio threshold.

        Example:
            >>> validator = CitationValidation(sequence_threshold=0.8)
            >>> print(validator.sequence_threshold)
            0.8
        """
        self.sequence_threshold = sequence_threshold
        self.jaccard_threshold = jaccard_threshold
        self.token_overlap = token_overlap

    def calculate_token_overlap(self, sentence1, sentence2) -> tuple:
        """
        Calculates the percentage of token overlap between two sentences.

        This method tokenizes both sentences and calculates the percentage of
        shared tokens relative to each sentence's length.

        Args:
            sentence1 (str): First sentence to compare.
            sentence2 (str): Second sentence to compare.

        Returns:
            tuple: (overlap_ratio_1, overlap_ratio_2) where each ratio is the
                  proportion of shared tokens to total tokens in that sentence.

        Example:
            >>> validator = CitationValidation()
            >>> ratio1, ratio2 = validator.calculate_token_overlap(
            ...     "The cat is black",
            ...     "The cat is white"
            ... )
            >>> print(f"{ratio1:.2f}, {ratio2:.2f}")
            '0.75, 0.75'
        """
        # Tokenize the sentences
        tokens1 = word_tokenize(sentence1)
        tokens2 = word_tokenize(sentence2)

        # Calculate the set intersection to find the overlapping tokens
        overlapping_tokens = set(tokens1) & set(tokens2)
        # Calculate the percentage of token overlap
        if len(tokens1) == 0:
            overlap_percentage = 0
        else:
            overlap_percentage = len(overlapping_tokens) / (len(tokens1))
        if len(tokens2) == 0:
            overlap_percentage_2 = 0
        else:
            overlap_percentage_2 = len(overlapping_tokens) / (len(tokens2))
        return overlap_percentage, overlap_percentage_2

    def jaccard_index(sself, sentence1, sentence2) -> float:
        """
        Calculates the Jaccard index between two sentences.

        This method computes the Jaccard index (intersection over union)
        between the sets of tokens from both sentences.

        Args:
            sentence1 (str): First sentence to compare.
            sentence2 (str): Second sentence to compare.

        Returns:
            float: Jaccard similarity score between 0 and 1.

        Example:
            >>> validator = CitationValidation()
            >>> score = validator.jaccard_index(
            ...     "The cat is black",
            ...     "The cat is white"
            ... )
            >>> print(f"{score:.2f}")
            '0.60'
        """
        # Convert the sentences to sets of words
        set1 = set(word_tokenize(sentence1))
        set2 = set(word_tokenize(sentence2))

        # Calculate the Jaccard index
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        jaccard_index = intersection / union if union != 0 else 0.0

        return jaccard_index

    def longest_common_subsequence(self, text1: str, text2: str) -> int:
        """Calculate length of longest common subsequence.

        This method finds the length of the longest subsequence of characters
        that appear in both texts in the same order.

        Args:
            text1 (str): First text to compare.
            text2 (str): Second text to compare.

        Returns:
            int: Length of longest common subsequence.

        Example:
            >>> validator = CitationValidation()
            >>> length = validator.longest_common_subsequence(
            ...     "hello world",
            ...     "hello there"
            ... )
            >>> print(length)
            6
        """
        dp = [[0 for i in range(len(text1) + 1)] for i in range(len(text2) + 1)]

        for i in range(1, len(text2) + 1):
            for j in range(1, len(text1) + 1):
                diagnoal = dp[i - 1][j - 1]
                if text1[j - 1] == text2[i - 1]:
                    diagnoal += 1
                dp[i][j] = max(diagnoal, dp[i - 1][j], dp[i][j - 1])
        return dp[-1][-1]

    def flatten_nested_list(self, nested_list: list[list[str]]) -> list[str]:
        """Flatten a nested list of strings.

        Args:
            nested_list (list[list[str]]): List of lists of strings.

        Returns:
            list[str]: Single list containing all non-empty strings.

        Example:
            >>> validator = CitationValidation()
            >>> flat = validator.flatten_nested_list([["a", "b"], ["c", ""]])
            >>> print(flat)
            ['a', 'b', 'c']
        """
        sentences = []
        for sublist in nested_list:
            for item in sublist:
                if len(item) > 0:
                    sentences.append(item)
        return sentences

    def split_paragraph_into_sentences(self, paragraph: str) -> list[str]:
        """Split paragraph into sentences using NLTK.

        Args:
            paragraph (str): Text to split into sentences.

        Returns:
            list[str]: List of sentences from the paragraph.

        Example:
            >>> validator = CitationValidation()
            >>> sentences = validator.split_paragraph_into_sentences(
            ...     "Hello there. How are you?"
            ... )
            >>> print(sentences)
            ['Hello there.', 'How are you?']
        """
        sentences = sent_tokenize(paragraph)
        return sentences

    def resources_from_belief(self, belief: Belief) -> list[ActionResource]:
        """Extract resources from belief state actions.

        Args:
            belief (Belief): Agent's belief state containing actions.

        Returns:
            list[ActionResource]: List of resources from retrieval actions.

        Example:
            >>> validator = CitationValidation()
            >>> belief = Belief()  # Contains retrieval action with resource
            >>> resources = validator.resources_from_belief(belief)
            >>> print(len(resources))
            1
        """
        resources = []
        for action in belief.actions:
            if isinstance(action, BaseRetrievalAction):
                resources.extend(action.resources)
        return resources

    def process_output(self, text: str, belief: Belief, **kwargs) -> ValidationResult:
        """Process text and add citations from belief resources.

        This method analyzes the input text against resources in the belief
        state and adds citations where appropriate based on similarity metrics.

        Args:
            text (str): Text to process and add citations to.
            belief (Belief): Agent's belief state containing resources.
            **kwargs: Additional arguments for processing.

        Returns:
            ValidationResult: Result containing text with citations added.

        Example:
            >>> validator = CitationValidation()
            >>> belief = Belief()  # Contains source about "Python"
            >>> result = validator.process_output(
            ...     "Python is a great language.",
            ...     belief
            ... )
            >>> print("[1]" in result.result)  # Has citation
            True
        """
        resources = self.resources_from_belief(belief)

        if len(resources) == 0:
            # no resources used, return the original text
            return ValidationResult(
                is_valid=True,
                result=text,
                feedback="",
            )

        return self.add_citations(text, resources)

    def add_citation_to_sentence(self, sentence: str, resources: list[ActionResource]):
        """Add citations to a single sentence.

        This method checks the sentence against each resource using similarity
        metrics to determine which sources to cite.

        Args:
            sentence (str): Sentence to add citations to.
            resources (list[ActionResource]): Available citation sources.

        Returns:
            citation_ids: a list of citation identifiers
            citation_links: a list of citation links (URLs)

        Example:
            >>> validator = CitationValidation()
            >>> resource = ActionResource(
            ...     source="http://example.com",
            ...     content="Python is great"
            ... )
            >>> ids, urls = validator.add_citation_to_sentence(
            ...     "Python is great!",
            ...     [resource]
            ... )
            >>> print(len(ids), urls[0])
            1 http://example.com
        """
        citation_ids = []
        citation_links = []

        if len(sentence) <= 5:
            return citation_ids, citation_links

        for index, resource in enumerate(resources):
            cited = False
            resource_link = resource.source
            resource_text = resource.content
            resource_sentences = resource_text.split(".")
            # TODO: verify that splitting each sentence on newlines improves citation results
            nested_sentence_lines = [s.split("\n") for s in resource_sentences]
            resource_lines = self.flatten_nested_list(nested_sentence_lines)

            for resource_line in resource_lines:
                if not cited and not (resource_link in citation_links):
                    seq = self.longest_common_subsequence(sentence, resource_line)
                    if (
                        (seq / len(sentence)) > self.sequence_threshold
                        or sentence in resource_line
                        or self.jaccard_index(sentence, resource_line)
                        > self.jaccard_threshold
                    ):
                        citation_links.append(resource_link)
                        citation_ids.append(index + 1)
                        cited = True

        return citation_ids, citation_links

    def format_sentence_with_citations(self, sentence, ids, links):
        """Format a sentence with its citations.

        This method adds citation references to the end of a sentence in
        the format [id](url).

        Args:
            sentence (str): Sentence to add citations to.
            ids (list[int]): Citation ID numbers.
            links (list[str]): Citation URLs.

        Returns:
            str: Sentence with citations added.

        Example:
            >>> validator = CitationValidation()
            >>> result = validator.format_sentence_with_citations(
            ...     "Python is great.",
            ...     [1],
            ...     ["http://example.com"]
            ... )
            >>> print(result)
            'Python is great [1](http://example.com).'
        """
        if len(ids) == 0:
            return sentence

        citations = []
        for id, url in zip(ids, links):
            reference = f"[{id}]({url})"
            citations.append(reference)

        new_sentence = sentence[:-1] + " " + ", ".join(citations) + "."
        return new_sentence

    def add_citations(self, text: str, resources: list[dict]) -> ValidationResult:
        paragraph = text.split("\n")
        paragraph = [p for p in paragraph if len(p.strip()) > 0]

        paragraphs = [self.split_paragraph_into_sentences(s) for s in paragraph]

        new_paragraph = []
        for paragraph in paragraphs:
            new_sentences = []

            # for each sentence in each paragraph
            for _, sentence in enumerate(paragraph):
                sentence = sentence.strip()
                if len(sentence) == 0:
                    continue

                ids, links = self.add_citation_to_sentence(sentence, resources)
                formatted_sentence = self.format_sentence_with_citations(
                    sentence, ids, links
                )
                new_sentences.append(formatted_sentence)

            new_paragraph.append(" ".join(new_sentences) + "\n")

        return ValidationResult(
            is_valid=True,
            result="".join(new_paragraph),
            feedback="",
        )

    def get_failure_message(self) -> str:
        return "Unable to add citations to the generated text. Please pay attention to the cited sources."
