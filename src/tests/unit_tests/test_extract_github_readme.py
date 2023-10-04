from sherpa_ai.scrape.extract_github_readme import extract_github_readme

def test_extract_github_readme_with_valid_url():

    repo_url = "https://github.com/Aggregate-Intellect/sherpa"
    content = extract_github_readme(repo_url)

    assert len(content)>0  

def test_extract_github_readme_with_invalid_url():
    repo_url = "https://google.com"
    content = extract_github_readme(repo_url)

    assert content == None 