# chatbot.py
from openai import OpenAI
from dotenv import load_dotenv
from ..paths import BASE_PATH
import os


class Chatty:

    def __init__(self):
        self.user_id = None
        self.bot_name = {}
        load_dotenv(dotenv_path=os.path.join(BASE_PATH, ".env"))
        self.client = {}
        self.system = [{"role": "system", "content": "You are a helpful AI assistant."}]
        self.chat = {}

    def set_client(self, user_id):
        self.client[user_id] = OpenAI(
            base_url=os.getenv("OAI_BASE_URL"), api_key=os.getenv("OAI_API_KEY")
        )
        self.bot_name[user_id] = f"Chatty for User {user_id}"
        self.chat[user_id] = []

    def get_client(self, user_id):
        if user_id in self.client:
            return self.client[user_id]
        return None

    def get_history(self, user_id):
        return self.chat[user_id]

    def get_bot_name(self, user_id):
        return self.bot_name[user_id]

    def chat_completion(self, user_id, new_message: str) -> dict:
        um = [{"role": "user", "content": new_message}]

        response = (
            self.client[user_id]
            .chat.completions.create(
                model="Meta-Llama-3-8B-Instruct",
                messages=self.system + self.chat[user_id][-10:] + um,
                temperature=0,
                max_tokens=1024,
            )
            .choices.pop()
            .message.content
        )
        response = response.replace("<|end_header_id|>", "", 1)
        response = response.replace("<|eot_id|>", "", 1)
        response = response.strip()  # remove newline at the beginning and end
        self.chat[user_id].append(um[0])
        self.chat[user_id].append({"role": "assistant", "content": response})
        return {"response": response}
