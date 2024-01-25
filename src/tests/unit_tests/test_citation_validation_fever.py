from sherpa_ai.output_parsers.citation_validation import CitationValidation
import sys

import pytest
from loguru import logger

from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.actions import GoogleSearch
from sherpa_ai.utils import extract_urls

def test_citation_validation():
    text = """Born in Scranton, Pennsylvania, Biden moved with his family to Delaware in 1953. 
    He graduated from the University of Delaware before earning his law degree from Syracuse University. 
    He was elected to the New Castle County Council in 1970 and to the U.S. 
    Senate in 1972. As a senator, Biden drafted and led the effort to pass the Violent Crime Control and Law Enforcement Act and the Violence Against Women Act. He also oversaw six U.S. Supreme Court confirmation hearings, including the contentious hearings for Robert Bork and Clarence Thomas. 
    Biden ran unsuccessfully for the Democratic presidential nomination in 1988 and 2008. In 2008, Obama chose Biden as his running mate, and he was a close counselor to Obama during his two terms as vice president. In the 2020 presidential election, Biden and his running mate, Kamala Harris, defeated incumbents Donald Trump and Mike Pence. He became the oldest president in U.S. history, and the first to have a female vice president.
    """
    data = {"Document": text, "Source": "www.wiki_1.com"}
    data_2 = {"Document": text, "Source": "www.wiki_2.com"}
    resource = [data, data_2]
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    assert (data["Source"] in result)
    

def test_citation_validation_2():
    print("\n")
    # 1
    text = """Nikolaj Coster-Waldau worked with the Fox Broadcasting Company."""
    
    source = """Nikolaj Coster-Waldau; born 27 July 1970 -RRB- is a Danish actor , producer and screenwriter . He graduated from Danish National School of Theatre in Copenhagen in 1993 . Coster-Waldau 's breakthrough performance in Denmark was his role in the film Nightwatch -LRB- 1994 -RRB- . Since then he has appeared in numerous films in his native Scandinavia and Europe in general , including Headhunters -LRB- 2011 -RRB- and A Thousand Times Good Night -LRB- 2013 -RRB- .   In the United States , his debut film role was in the war film Black Hawk Down -LRB- 2001 -RRB- , playing Medal of Honor recipient Gary Gordon . He then played Detective John Amsterdam in the short-lived Fox television series New Amsterdam -LRB- 2008 -RRB- , as well as appearing as Frank Pike in the 2009 Fox television film Virtuality , originally intended as a pilot . He became widely known to a broad audience for his current role as Ser Jaime Lannister , in the HBO series Game of Thrones . In 2017 , he became one of the highest paid actors on television and earned # 2 million per episode of Game of Thrones . 
    """
    data = {"Document": source, "Source": "www.Nikolaj_Coster-Waldau.com"}
    resource = [data]
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    
    # 2
    text = "Nikolaj Coster-Waldau was in a film."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    
    # 3
    text = """In 1994, Nikolaj Coster-Waldau appeared in the movie "Nightwatch"."""
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    
    # 4
    text = "Nikolaj Coster-Waldau was in a Danish thriller film."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)

    # 5
    text = "Nikolaj Coster-Waldau was in multiple Fox Broadcasting Company productions."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    
    # 6
    text = "Nikolaj Coster-Waldau played Detective John Amsterdam in New Amsterdam."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)

    # 7
    text = "Nikolaj Coster-Waldau was in a suspense movie of Danish origin."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    
    # 8 
    text = "Nikolaj Coster-Waldau is an actor."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    
    # 9 
    text = "Nikolaj Coster-Waldau worked with Peter Dinklage."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)
    
    # 10 
    text = "Game of Thrones (season 1) featured Danish actor Nikolaj Coster-Waldau."
    module = CitationValidation()
    result = module.parse_output(text, resource)
    print(result)