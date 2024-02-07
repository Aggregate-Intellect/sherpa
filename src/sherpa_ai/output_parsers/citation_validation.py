import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

from sherpa_ai.output_parsers.base import BaseOutputParser
from sherpa_ai.output_parsers.validation_result import ValidationResult

nltk.download("punkt")


class CitationValidation(BaseOutputParser):
    def __init__(self, seq_thresh=0.7, jaccard_thresh=0.7, token_overlap=0.7):
        # threshold
        self.seq_thresh = seq_thresh  # threshold for common longest subsequece / text
        self.jaccard_thresh = jaccard_thresh
        self.token_overlap = token_overlap

    def calculate_token_overlap(self, sentence1, sentence2):
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

    def jaccard_index(sself, sentence1, sentence2):
        # Convert the sentences to sets of words
        set1 = set(word_tokenize(sentence1))
        set2 = set(word_tokenize(sentence2))

        # Calculate the Jaccard index
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        jaccard_index = intersection / union if union != 0 else 0.0

        return jaccard_index

    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        # A subsequence of a string is a new string generated from the
        # original string with some characters
        # (can be none) deleted without changing the relative
        # order of the remaining characters.
        dp = [[0 for i in range(len(text1) + 1)] for i in range(len(text2) + 1)]

        for i in range(1, len(text2) + 1):
            for j in range(1, len(text1) + 1):
                diagnoal = dp[i - 1][j - 1]
                if text1[j - 1] == text2[i - 1]:
                    diagnoal += 1
                dp[i][j] = max(diagnoal, dp[i - 1][j], dp[i][j - 1])
        return dp[-1][-1]

    def unfoldList(self, nestedList: list[list[str]]):
        sentences = []
        for sublist in nestedList:
            for item in sublist:
                if len(item) > 0:
                    sentences.append(item)
        return sentences

    def split_paragraph_into_sentences(self, paragraph):
        sentences = sent_tokenize(paragraph)
        return sentences

    # add citation to the generated text
    def parse_output(self, generated: str, resources: list[dict]) -> ValidationResult:
        """ 
        Add citation to each sentence in the generated text from resources based on fact checking model.
        Args:
            generated (str): The generated content where we need to add citation/reference
            resources (list[dict]): A list of dictionaries containing reference text and links.
                Each dictionary in the list should have the format {"Document": str, "Source": str}.
            activated (bool): control whether we need to add citation or just return the raw generated text.
                by default it is activated.
        Returns:
            str: A formatted string combining the citation information from the 'resources' list.
        """

        # resources type
        # resources = [{"Document":, "Source":...}, {}]
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
