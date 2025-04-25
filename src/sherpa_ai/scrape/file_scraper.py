"""File scraping and handling module for Sherpa AI.

This module provides functionality for downloading, processing, and analyzing
files attached to questions. It handles various file types including PDF,
text, markdown, HTML, and XML files.
"""

import os

import requests

import sherpa_ai.config as cfg
from sherpa_ai.utils import (
    chunk_and_summarize_file,
    count_string_tokens,
    extract_text_from_pdf,
    question_with_file_reconstructor,
)


DOWNLOAD_TIMEOUT = 2.5


class QuestionWithFileHandler:
    """Handler for questions with attached files.

    This class manages the process of downloading, processing, and analyzing
    files attached to questions. It supports various file types and handles
    token limits and content summarization.

    Attributes:
        question (str): The user's question to be answered.
        token (str): OAuth token for file access.
        files (list): List of file information dictionaries.
        user_id (str): ID of the user asking the question.
        llm (Any): Language model for text processing.

    Example:
        >>> handler = QuestionWithFileHandler(
        ...     question="What's in the document?",
        ...     files=[{"id": "123", "filetype": "pdf"}],
        ...     token="oauth_token",
        ...     user_id="user123",
        ...     llm=language_model
        ... )
        >>> result = handler.reconstruct_prompt_with_file()
        >>> print(result["status"])
        'success'
    """

    def __init__(self, question, files, token, user_id, team_id, llm):
        """Initialize the file handler.

        Currently works for one file only.

        Args:
            question (str): The user's question.
            files (list): List of file information dictionaries.
            token (str): OAuth token for file access.
            user_id (str): ID of the user asking the question.
            team_id (str): ID of the team context.
            llm (Any): Language model for text processing.
        """
        self.question = question
        self.token = token
        self.files = files
        self.user_id = user_id
        self.llm = llm

    def reconstruct_prompt_with_file(self):
        """Reconstruct the prompt using the attached file.

        This method downloads the file, processes its content, and combines
        it with the original question to create a more informed prompt.

        Returns:
            dict: A dictionary containing:
                - status (str): 'success' or 'error'
                - data (str): Reconstructed prompt if successful
                - message (str): Error message if failed

        Example:
            >>> result = handler.reconstruct_prompt_with_file()
            >>> if result["status"] == "success":
            ...     print(result["data"])
            'Based on the PDF content...'
        """
        file_text_format = self.download_file(self.files[0])
        if file_text_format["status"] == "success":
            reconstructed_prompt = self.prompt_reconstruct(
                file_info=self.files[0], data=file_text_format["data"]
            )
            if reconstructed_prompt["status"] == "success":
                return {"status": "success", "data": reconstructed_prompt["data"]}
            else:
                return {"status": "error", "message": reconstructed_prompt["message"]}
        else:
            return {"status": "error", "message": file_text_format["message"]}

    def download_file(self, file):
        """Download and extract content from a file.

        This method downloads a file using its URL and extracts its content
        based on the file type. Supports PDF, text, markdown, HTML, and XML.

        Args:
            file (dict): File information dictionary containing:
                - id (str): File identifier
                - mimetype (str): MIME type
                - url_private_download (str): Download URL
                - filetype (str): File extension

        Returns:
            dict: A dictionary containing:
                - status (str): 'success' or 'error'
                - data (str): File content if successful
                - message (str): Error message if failed

        Example:
            >>> file_info = {
            ...     "id": "123",
            ...     "filetype": "pdf",
            ...     "url_private_download": "https://example.com/doc.pdf"
            ... }
            >>> result = handler.download_file(file_info)
            >>> if result["status"] == "success":
            ...     print(len(result["data"]))
            1024
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": file["mimetype"],
        }
        response = requests.get(
            file["url_private_download"], headers=headers, timeout=DOWNLOAD_TIMEOUT
        )
        destination = file["id"] + file["filetype"]

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            content_data = ""
            if file["filetype"] == "pdf":
                # Open the local file and write the content of the downloaded file
                with open(destination, "wb") as temp_file:
                    temp_file.write(response.content)
                    content_data = extract_text_from_pdf(destination)
                os.remove(destination)

            elif file["filetype"] in ["txt", "md", "text", "markdown", "html", "xml"]:
                content_data = response.content.decode("utf-8")
            else:
                return {
                    "status": "error",
                    "message": f"we currently don't support {file['filetype']} file format.",
                }
            return {"status": "success", "data": content_data}

        else:
            return {
                "status": "error",
                "message": f"Failed to download the file. HTTP status code: {response.status_code}",
            }

    def prompt_reconstruct(self, file_info, data=str):
        """Reconstruct the prompt with file content.

        This method processes the file content, handles token limits, and
        combines the content with the original question to create an
        enhanced prompt.

        Args:
            file_info (dict): File information dictionary containing:
                - filetype (str): File extension
                - name (str): File name
                - title (str): File title
            data (str): Content of the file.

        Returns:
            dict: A dictionary containing:
                - status (str): 'success' or 'error'
                - data (str): Reconstructed prompt if successful
                - message (str): Error message if failed

        Example:
            >>> file_info = {
            ...     "filetype": "pdf",
            ...     "name": "document.pdf",
            ...     "title": "Important Doc"
            ... }
            >>> result = handler.prompt_reconstruct(file_info, "content...")
            >>> if result["status"] == "success":
            ...     print(result["data"])
            'Based on the PDF "Important Doc"...'
        """
        chunk_summary = data
        data_token_size = count_string_tokens(self.question + data, "gpt-3.5-turbo")

        if data_token_size > cfg.FILE_TOKEN_LIMIT:
            return {
                "status": "error",
                "message": "token ammount of a file has to be less than {}",
            }
        else:
            chunk_summary = chunk_and_summarize_file(
                file_format=file_info["filetype"],
                file_name=file_info["name"],
                question=self.question,
                title=file_info["title"],
                text_data=data,
                llm=self.llm,
            )

            while count_string_tokens(chunk_summary, "gpt-3.5-turbo") > 3000:
                chunk_summary = chunk_and_summarize_file(
                    file_format=file_info["filetype"],
                    file_name=file_info["name"],
                    question=self.question,
                    title=file_info["title"],
                    text_data=chunk_summary,
                    llm=self.llm,
                )
        result = question_with_file_reconstructor(
            file_format=file_info["filetype"],
            data=chunk_summary,
            title=file_info["title"],
            file_name=file_info["name"],
            question=self.question,
        )
        return {"status": "success", "data": result}
