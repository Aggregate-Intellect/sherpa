import re

from output_parsers.base import BaseOutputParser


class LinkParser(BaseOutputParser):
    def __init__(self):
        self.links = []
        self.link_to_id = {}
        self.count = 0

        self.url_pattern = r"Link:(\S+?)(?:\s|$)"
        self.doc_id_pattern = r"(?:\[)(\d+)(?:\])"

        self.link_symbol = "[{id}]"

    def parse_output(self, text: str) -> str:
        def replace_with_symbol(match: re.Match):
            link = match.group(1)

            if link not in self.link_to_id:
                self.link_to_id[link] = self.link_symbol.format(id=self.count)
                self.links.append(link)
                self.count += 1

            return "DocID:" + self.link_to_id[link] + "\n\n"

        def replace_with_link(match: re.Match):
            print(match)
            doc_id = match.group(1)
            return f"[[{doc_id}]]({self.links[int(doc_id)]})"

        if re.search(self.url_pattern, text):
            modified_text = re.sub(self.url_pattern, replace_with_symbol, text)
        else:
            modified_text = re.sub(self.doc_id_pattern, replace_with_link, text)
        print(modified_text)
        # print(modified_text)

        return modified_text
