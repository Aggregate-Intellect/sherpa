import requests
import os
from sherpa_ai.utils import chunk_and_summarize_file, count_string_tokens, extract_text_from_pdf, question_with_file_reconstructor
import sherpa_ai.config as cfg

class QuestionWithFileHandler:
	def __init__(self, question,  files,  token  , user_id , team_id):
		self.question = question
		self.token = token
		self.files = files
		self.team_id = team_id
		self.user_id = user_id
	def reconstruct_prompt_with_file(self):
		file_text_format = self.download_file(self.files[0])
		if file_text_format['status']=="success":
			reconstructed_prompt = self.prompt_reconstruct(file_info =self.files[0] ,  data=file_text_format['data'])
			if reconstructed_prompt['status']=="success":
				return {'status':'success' , 'data':reconstructed_prompt['data']}
			else:
				return {'status':'error' , 'message':reconstructed_prompt['message']}
		else:
			return {'status':'error' , 'message':file_text_format["message"]}
	


	def download_file(self , file):
		headers = {
			"Authorization": f"Bearer {self.token}",
			"Accept": file["mimetype"],
		}
		response = requests.get(file['url_private_download'], headers=headers )
		destination = file['id']+file['filetype']

		# Check if the request was successful (HTTP status code 200)
		if response.status_code == 200:
			content_data = ""
			if file['filetype']=="pdf":
			# Open the local file and write the content of the downloaded file
				with open(destination, 'wb') as temp_file:
					temp_file.write(response.content)
					content_data = extract_text_from_pdf(destination)
				os.remove(destination)
				
			elif file["filetype"] in ["txt" , "md" ,  "text" ,"markdown" ,"html" , "xml"]:
				content_data = response.content.decode('utf-8')
			else:
				return  {"status":"error" , "message":f"we currently don't support {file['filetype']} file format."}
			return {"status":"success" , "data":content_data}

		else:
			return {"status":"error" , "message":f"Failed to download the file. HTTP status code: {response.status_code}"}

	def prompt_reconstruct(self , file_info  ,  data=str):
		chunk_summary = data
		data_token_size = count_string_tokens(self.question + data, "gpt-3.5-turbo")

		if data_token_size > cfg.FILE_TOKEN_LIMIT:
			return {"status":"error" , "message":"token ammount of a file has to be less than {}"}
		elif data_token_size>3000:
			chunk_summary = chunk_and_summarize_file(
				file_format=file_info['filetype'],
				file_name=file_info['name'],
				question=self.question,
				title=file_info['title'],
				text_data=data,
				team_id=self.team_id,
				user_id=self.user_id
			)

			
			while count_string_tokens(chunk_summary, "gpt-3.5-turbo") > 3000:
				chunk_summary = chunk_and_summarize_file(
					file_format=file_info['filetype'],
					file_name=file_info['name'],
					question=self.question,
					title=file_info['title'],
					text_data=chunk_summary
				)
		result = question_with_file_reconstructor(file_format=file_info['filetype'] , data=chunk_summary,title=file_info['title'],file_name=file_info['name'], question=self.question)
		return  {"status":"success" , "data":result}


