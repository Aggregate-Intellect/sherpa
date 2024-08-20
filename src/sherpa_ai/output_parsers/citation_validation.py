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
    """
    A class for adding citations to generated text based on a list of resources.

    This class inherits from the abstract class BaseOutputParser and provides
    methods to add citations to each sentence in the generated text based on
    reference texts and links provided in the 'resources' list.

    Attributes:
        sequence_threshold (float): Threshold for common longest subsequence / text. Default is 0.7.
        jaccard_threshold (float): Jaccard similarity threshold. Default is 0.7.
        token_overlap (float): Token overlap threshold. Default is 0.7.

    Typical usage example:
    ```python
    citation_parser = CitationValidation(seq_thresh=0.7, jaccard_thresh=0.7, token_overlap=0.7)
    result = citation_parser.parse_output(generated_text, list_of_resources)
    ```
    """

    def __init__(
        self, sequence_threshold=0.7, jaccard_threshold=0.7, token_overlap=0.7
    ):
        self.sequence_threshold = sequence_threshold
        self.jaccard_threshold = jaccard_threshold
        self.token_overlap = token_overlap

    def calculate_token_overlap(self, sentence1, sentence2) -> tuple:
        """
        Calculates the percentage of token overlap between two sentences.

        Tokenizes the input sentences and calculates the percentage of token overlap
        by finding the intersection of the token sets and dividing it by the length
        of each sentence's token set.

        Args:
            sentence1 (str): The first sentence for token overlap calculation.
            sentence2 (str): The second sentence for token overlap calculation.

        Returns:
            tuple: A tuple containing two float values representing the percentage
            of token overlap for sentence1 and sentence2, respectively.
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

        The Jaccard index is a measure of similarity between two sets, defined as the
        size of the intersection divided by the size of the union of the sets.

        Args:
            sentence1 (str): The first sentence for Jaccard index calculation.
            sentence2 (str): The second sentence for Jaccard index calculation.

        Returns:
            float: The Jaccard index representing the similarity between the two sentences.
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
        """
        Calculates the length of the longest common subsequence between two texts.

        A subsequence of a string is a new string generated from the original
        string with some characters (can be none) deleted without changing
        the relative order of the remaining characters.

        Args:
        - text1 (str): The first text for calculating the longest common subsequence.
        - text2 (str): The second text for calculating the longest common subsequence.

        Returns:
        - int: The length of the longest common subsequence between the two texts.
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
        """
        Flattens a nested list of strings into a single list of strings.

        Args:
            nested_list (list[list[str]]): The nested list of strings to be flattened.

        Returns:
            list[str]: A flat list containing all non-empty strings from the nested list.
        """
        sentences = []
        for sublist in nested_list:
            for item in sublist:
                if len(item) > 0:
                    sentences.append(item)
        return sentences

    def split_paragraph_into_sentences(self, paragraph: str) -> list[str]:
        """
        Uses NLTK's sent_tokenize to split the given paragraph into a list of sentences.

        Args:
            paragraph (str): The input paragraph to be tokenized into sentences.

        Returns:
            list[str]: A list of sentences extracted from the input paragraph.
        """
        sentences = sent_tokenize(paragraph)
        return sentences

    def resources_from_belief(self, belief: Belief) -> list[ActionResource]:
        """
        Returns a list of all resources within belief.actions.
        """
        resources = []
        for action in belief.actions:
            if isinstance(action, BaseRetrievalAction):
                resources.extend(action.resources)
        return resources

    def process_output(self, text: str, belief: Belief, **kwargs) -> ValidationResult:
        """
         Add citations to sentences in the generated text using resources based on fact checking model.

         Args:
             text (str): The text which needs citations/references added
             belief (Belief): Belief of the agent that generated `text`

         Returns:
             ValidationResult: The result of citation processing.
             `is_valid` is True when citation processing succeeds or no citation resources are provided,
             False otherwise.
             `result` contains the formatted text with citations.
             `feedback` providing additional optional information.

        Typical usage example:
         ```python
         resources = ActionResource(source="http://example.com/source1", content="Some reference text.")]
         citation_parser = CitationValidation()
         result = citation_parser.parse_output("Text needing citations.", resources)
         ```
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
        """
        Uses a list of resources to add citations to a sentence

        Returns:
            citation_ids: a list of citation identifiers
            citation_links: a list of citation links (URLs)
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
        """
        Appends citations to sentence
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
