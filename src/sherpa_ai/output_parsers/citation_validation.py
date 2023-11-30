from sherpa_ai.output_parsers.base import BaseOutputParser

import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt')


class CitationValidation(BaseOutputParser):
    def __init__(self):
        # threshold
        self.seq_thresh = 0.8  # threshold for common longest subsequece / text
        self.jaccard_thresh = 0.7
        self.token_overlap = 0.7

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
            overlap_percentage = (len(overlapping_tokens) / (len(tokens1)))
        if len(tokens2) == 0:
            overlap_percentage_2 = 0
        else:
            overlap_percentage_2 = (len(overlapping_tokens) / (len(tokens2)))
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

        for i in range(1, len(text2)+1):
            for j in range(1, len(text1)+1):
                diagnoal = dp[i-1][j-1]
                if text1[j-1] == text2[i-1]:
                    diagnoal += 1
                dp[i][j] = max(diagnoal, dp[i-1][j], dp[i][j-1])
        return dp[-1][-1]

    def unfoldList(self, nestedList: list[list[str]]):
        sentences = []
        for sublist in nestedList:
            for item in sublist:
                if len(item) > 0:
                    sentences.append(item)
        return sentences

    # add citation to the generated text
    def parse_output(self, generated: str, resources: list[dict()]) -> str:
        # resources type
        # resources = [{"Document":, "Source":...}, {}]
        paragraph = generated.split("\n")
        paragraph = [p for p in paragraph if len(p.strip()) > 0]
        sub_string = [s.split(".") for s in paragraph]  # nested list

        # sentences = unfoldList(sub_string)
        new_paragraph = []
        for paragraph in sub_string:
            new_sentence = []
            for _, sentence in enumerate(paragraph):
                links = []
                ids = []
                sentence = sentence.strip()
                for index, source in enumerate(resources):
                    cited = False  # if this resource is cited
                    text = source["Document"]
                    one_sentences = text.split(".")
                    sub_string = [s.split("\n") for s in one_sentences]
                    split_texts = self.unfoldList(sub_string)

                    link = source["Source"]
                    
                    for j in split_texts:
                        if len(sentence) > 5 and not cited and \
                            not (link in links):

                            seq = self.longestCommonSubsequence(sentence, j)

                            contained = False
                            if sentence in j:
                                # print("contained", s, j)
                                contained = True
                            jaccard = self.jaccard_index(sentence, j)
                            # print(jaccard)

                            if (seq/len(sentence)) > self.seq_thresh or \
                                contained or jaccard > self.jaccard_thresh:

                                links.append(link)
                                ids.append(index)
                citations = []
                for id, url in zip(ids, links):
                    reference = f"[{id}]({url})"
                    citations.append(reference)

                new_sentence.append(sentence + ', '.join(citations) + ".")
            new_paragraph.append(" ".join(new_sentence) + "\n")
        return "".join(new_paragraph)