import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.validation_result import ValidationResult

nltk.download("punkt")


class CitationValidation(BaseOutputProcessor):
    """
    A class for adding citations to generated text based on a list of resources.

    This class inherits from the abstract class BaseOutputParser and provides
    methods to add citations to each sentence in the generated text based on
    reference texts and links provided in the 'resources' list.

    Attributes:
    - seq_thresh (float): Threshold for common longest subsequence / text. Default is 0.7.
    - jaccard_thresh (float): Jaccard similarity threshold. Default is 0.7.
    - token_overlap (float): Token overlap threshold. Default is 0.7.

    Methods:
    - calculate_token_overlap(sentence1, sentence2): Calculate token overlap between two sentences.
    - jaccard_index(sentence1, sentence2): Calculate Jaccard similarity index between two sentences.
    - longestCommonSubsequence(text1, text2): Calculate the length of the longest common subsequence between two texts.
    - unfoldList(nestedList): Flatten a nested list of strings.
    - split_paragraph_into_sentences(paragraph): Tokenize a paragraph into sentences.
    - parse_output(generated, resources): Add citation to each sentence in the generated text from resources based on fact-checking model.

    Example Usage:
    ```python
    citation_parser = CitationValidation(seq_thresh=0.7, jaccard_thresh=0.7, token_overlap=0.7)
    result = citation_parser.parse_output(generated_text, list_of_resources)
    ```
    """

    def __init__(self, seq_thresh=0.7, jaccard_thresh=0.7, token_overlap=0.7):
        """
        Initialize the CitationValidation object.

        Args:
        - seq_thresh (float): Threshold for common longest subsequence / text. Default is 0.7.
        - jaccard_thresh (float): Jaccard similarity threshold. Default is 0.7.
        - token_overlap (float): Token overlap threshold. Default is 0.7.
        """
        self.seq_thresh = seq_thresh  # threshold for common longest subsequece / text
        self.jaccard_thresh = jaccard_thresh
        self.token_overlap = token_overlap

    def calculate_token_overlap(self, sentence1, sentence2) -> tuple:
        """
        Calculate the percentage of token overlap between two sentences.

        Tokenizes the input sentences and calculates the percentage of token overlap
        by finding the intersection of the token sets and dividing it by the length
        of each sentence's token set.

        Args:
        - sentence1 (str): The first sentence for token overlap calculation.
        - sentence2 (str): The second sentence for token overlap calculation.

        Returns:
        - tuple: A tuple containing two float values representing the percentage
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
        Calculate the Jaccard index between two sentences.

        The Jaccard index is a measure of similarity between two sets, defined as the
        size of the intersection divided by the size of the union of the sets.

        Args:
        - sentence1 (str): The first sentence for Jaccard index calculation.
        - sentence2 (str): The second sentence for Jaccard index calculation.

        Returns:
        - float: The Jaccard index representing the similarity between the two sentences.
        """
        # Convert the sentences to sets of words
        set1 = set(word_tokenize(sentence1))
        set2 = set(word_tokenize(sentence2))

        # Calculate the Jaccard index
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        jaccard_index = intersection / union if union != 0 else 0.0

        return jaccard_index

    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        """
        Calculate the length of the longest common subsequence between two texts.

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

    def unfoldList(self, nestedList: list[list[str]]) -> list[str]:
        """
        Flatten a nested list of strings into a single list of strings.

        Args:
        - nestedList (list[list[str]]): The nested list of strings to be flattened.

        Returns:
        - list[str]: A flat list containing all non-empty strings from the nested list.
        """
        sentences = []
        for sublist in nestedList:
            for item in sublist:
                if len(item) > 0:
                    sentences.append(item)
        return sentences

    def split_paragraph_into_sentences(self, paragraph: str) -> list[str]:
        """
        Tokenize a paragraph into a list of sentences.

        Uses NLTK's sent_tokenize to split a given paragraph into a list of sentences.

        Args:
        - paragraph (str): The input paragraph to be tokenized into sentences.

        Returns:
        - list[str]: A list of sentences extracted from the input paragraph.
        """
        sentences = sent_tokenize(paragraph)
        return sentences

    def find_used_resources(self, belief: Belief) -> list[dict]:
        resources = []
        for action in belief.actions:
            if hasattr(action, "meta") and action.meta is not None:
                resources.extend(action.meta[-1])
        return resources

    # add citation to the generated text
    def process_output(self, generated: str, belief: Belief) -> ValidationResult:
        """
        Add citation to each sentence in the generated text from resources based on fact checking model.
        Args:
            generated (str): The generated content where we need to add citation/reference
            agent (BaseAgent): Belief of the agents generated the content
        Returns:
        - ValidationResult: An object containing the result of citation addition and feedback.
        The ValidationResult has attributes 'is_valid' indicating success, 'result' containing
        the formatted text with citations, and 'feedback' providing additional information.

        Note:
        - The 'resources' list should contain dictionaries with "Document" and "Source" keys.

        Example:
        ```python
        resources = [{"Document": "Some reference text.", "Source": "http://example.com/source1"}]
        citation_parser = CitationValidation()
        result = citation_parser.parse_output("Generated text.", resources)
        ```

        """
        # resources type
        # resources = [{"Document":, "Source":...}, {}]
        resources = self.find_used_resources(belief)

        if len(resources) == 0:
            # no resources used, return the original text
            return ValidationResult(
                is_valid=True,
                result=generated,
                feedback="",
            )

        return self.add_citations(generated, resources)

    def add_citations(self, generated: str, resources: list[dict]) -> ValidationResult:
        paragraph = generated.split("\n")
        paragraph = [p for p in paragraph if len(p.strip()) > 0]

        paragraphs = [
            self.split_paragraph_into_sentences(s) for s in paragraph
        ]  # nested list

        new_paragraph = []
        for one_paragraph in paragraphs:
            new_sentence = []
            for _, sentence in enumerate(one_paragraph):
                links = []
                ids = []
                sentence = sentence.strip()
                if len(sentence) == 0:
                    continue

                for index, source in enumerate(resources):
                    cited = False  # if this resource is cited
                    text = source["Document"]
                    one_sentences = text.split(".")
                    sub_string = [s.split("\n") for s in one_sentences]
                    split_texts = self.unfoldList(sub_string)

                    link = source["Source"]

                    for j in split_texts:
                        if len(sentence) > 5 and not cited and not (link in links):
                            seq = self.longestCommonSubsequence(sentence, j)

                            contained = False
                            if sentence in j:
                                # print("contained", s, j)
                                contained = True
                            jaccard = self.jaccard_index(sentence, j)
                            # print(jaccard)

                            if (
                                (seq / len(sentence)) > self.seq_thresh
                                or contained
                                or jaccard > self.jaccard_thresh
                            ):
                                links.append(link)
                                ids.append(index + 1)
                citations = []
                for id, url in zip(ids, links):
                    reference = f"[{id}]({url})"
                    citations.append(reference)

                if len(citations) > 0:
                    new_sentence.append(
                        sentence[:-1] + " " + ", ".join(citations) + "."
                    )
                else:
                    new_sentence.append(sentence)

            new_paragraph.append(" ".join(new_sentence) + "\n")

        return ValidationResult(
            is_valid=True,
            result="".join(new_paragraph),
            feedback="",
        )

    def get_timeout_message(self) -> str:
        return "Citations was not able to be added to the generated text. Please pay attention to the cited sources."
