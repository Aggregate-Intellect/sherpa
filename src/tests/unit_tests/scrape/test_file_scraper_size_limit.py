from unittest.mock import MagicMock, patch

from sherpa_ai.scrape.file_scraper import QuestionWithFileHandler


def _make_handler():
    return QuestionWithFileHandler(
        question="what does this say?",
        files=[{
            "id": "f1",
            "filetype": "txt",
            "mimetype": "text/plain",
            "url_private_download": "https://example.com/f.txt",
        }],
        token="token",
        user_id="user1",
        team_id="team1",
        llm=None,
    )


def _mock_response(content: bytes):
    response = MagicMock()
    response.status_code = 200
    response.content = content
    return response


def test_download_file_rejects_oversized_file():
    handler = _make_handler()
    oversized_content = b"x" * 10

    with patch("sherpa_ai.scrape.file_scraper.safe_get", return_value=_mock_response(oversized_content)), \
         patch("sherpa_ai.scrape.file_scraper.cfg.FILE_SIZE_LIMIT", 5):
        result = handler.download_file(handler.files[0])

    assert result["status"] == "error"
    assert "size" in result["message"].lower()


def test_download_file_accepts_file_within_limit():
    handler = _make_handler()
    small_content = b"hello world"

    with patch("sherpa_ai.scrape.file_scraper.safe_get", return_value=_mock_response(small_content)), \
         patch("sherpa_ai.scrape.file_scraper.cfg.FILE_SIZE_LIMIT", 1000):
        result = handler.download_file(handler.files[0])

    assert result["status"] == "success"
    assert result["data"] == "hello world"
