import re

from loguru import logger

from sherpa_ai.output_parsers.base import BaseOutputParser


class LinkParser(BaseOutputParser):
    def __init__(self):
        self.links = []
        self.link_to_id = {}
        self.count = 1

        # for output reindexing
        self.output_counter = 1
        self.reindex_mapping = {}

        self.url_pattern = r"Link:(\S+?)(?:\s|$)"
        self.doc_id_pattern = r"(?:\[)(\d+)(?:\])"

        self.link_symbol = "[{id}]"

    def parse_output(self, text: str, tool_output=False) -> str:
        def replace_with_symbol(match: re.Match):
            link = match.group(1)
            # check if the link is valid
            if not link.startswith("http"):
                link = "http://" + link
            if link not in self.link_to_id:
                self.link_to_id[link] = self.link_symbol.format(id=self.count)
                self.links.append(link)
                self.count += 1

            return "DocID:" + self.link_to_id[link] + "\n\n"

        def replace_with_link(match: re.Match):
            logger.debug(match)
            doc_id = int(match.group(1))
            if doc_id <= 0 or doc_id > len(self.links):
                return ""

            if doc_id not in self.reindex_mapping:
                self.reindex_mapping[doc_id] = self.output_counter
                self.output_counter += 1

            result = f"<{self.links[doc_id - 1]}|[{self.reindex_mapping[doc_id]}]>"
            return result

        logger.warning(self.link_to_id)

        if tool_output:
            modified_text = re.sub(self.url_pattern, replace_with_symbol, text)
        else:
            logger.warning(text)
            modified_text = re.sub(self.doc_id_pattern, replace_with_link, text)
            logger.warning(modified_text)
        logger.debug(modified_text)

        return modified_text
