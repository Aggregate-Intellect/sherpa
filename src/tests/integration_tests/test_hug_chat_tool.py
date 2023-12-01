from sherpa_ai.tools import HugChatTool

def test_hug_chat_tool():
     question = "What is langchain?"
     response = HugChatTool().run(question)
     assert "langchain" in response.text.lower(), "langchain not found in response"