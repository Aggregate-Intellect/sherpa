from sherpa_ai.agents.base import BaseAgent
import urllib, urllib.request
import re


ml_engineer_description = """You are a skilled machine learning engineer. \
Your expertise lies in developing and implementing machine learning models to solve complex problems. \
You can answers questions or research about ML-related topics. \
If you encounter a question or challenge outside your current knowledge base, you acknowledge your limitations and seek assistance or additional resources to fill the gaps. \
"""

class MLEngineer(BaseAgent):
    """
    The ML engineer answers questions or research about ML-related topics
    """
    def __init__(
        self,
        name = "machine learning engineer",
        description = ml_engineer_description,
    ):
        self.name = name
        self.description = description
    

    def search_arxiv(self, query: str, top_k: int):
        url = 'http://export.arxiv.org/api/query?search_query=all:' + query + "&start=0&max_results=" + str(top_k)
        data = urllib.request.urlopen(url)
        xml_content = data.read().decode('utf-8')

        summary_pattern = r'<summary>(.*?)</summary>'
        summaries = re.findall(summary_pattern, xml_content, re.DOTALL)
        title_pattern = r'<title>(.*?)</title>'
        titles = re.findall(title_pattern, xml_content, re.DOTALL)

        result_list = []
        for i in range(len(titles)):
            result_list.append("Title: " + titles[i] + "\n" + "Summary: " + summaries[i])
        
        return result_list