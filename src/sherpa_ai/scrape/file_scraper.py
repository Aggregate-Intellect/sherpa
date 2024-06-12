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
    def __init__(self, question, files, token, user_id, team_id, llm):
        """
        Initializes the QuestionWithFileHandler instance.

        currently works for one file only.

        Args:
            question (str): The user's question.
            files (list): List of files associated with the question.
            token (str): OAuth token.
            user_id (str): User ID.
        """

        self.question = question
        self.token = token
        self.files = files
        self.user_id = user_id
        self.llm = llm

    def reconstruct_prompt_with_file(self):
        """
        Reconstructs the prompt using the associated file.

        Returns:
            dict: A dictionary with status and reconstructed prompt data.
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
        """
        Gets the specified file via HTTP and returns the file content.

        Args:
            file (dict): Information about the file to be downloaded. Example name, title, filetype etc

        Returns:
            dict: A dictionary with status and downloaded file content.
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
        """
        Reconstructs the prompt with the file content.

        Args:
            file_info (dict): Information about the file being reconstructed. Example name, title, filetype etc
            data (str): Content of the file.

        Returns:
            dict: A dictionary with status and reconstructed prompt data.
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
