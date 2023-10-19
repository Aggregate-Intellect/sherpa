from sherpa_ai.task_agent import TaskAgent


def test_task_agent():
    task_agent = TaskAgent()
    task = "What is AutoGPT"
    result = task_agent.run(task)
    assert result is not ""