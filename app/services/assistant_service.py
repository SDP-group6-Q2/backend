import os

from assistant.src.FleetAssistant import FleetAssistant

from app.models.user import UserModel

class AssistantService:
    def __init__(self, assistant: FleetAssistant | None = None):
        llama_model = os.getenv("LLAMA_MODEL", "gpt-oss:20b-cloud")
        llama_base_url = os.getenv("LLAMA_BASE_URL", "http://localhost:11434")
        self.assistant = assistant if assistant is not None else FleetAssistant(llama_model=llama_model, llama_base_url=llama_base_url)

    def ask_assistant(self, machine_id: str, user: UserModel, message: str) -> str:
        try: 
            response = self.assistant.ask(message, str(user.client_id), machine_id)
            return response
        except Exception as e:
            raise Exception(f"Error while asking the assistant: {e}")
    
def get_assistant_service() -> AssistantService:
    return AssistantService()