from typing import Dict
from chatty.services.chatty_spacy_service import ChattySpacyService


class ChattyOrchestration:

    async def message(self, request) -> Dict:
        message = request.query.get('message', '')
        chatty_spacy_service = ChattySpacyService()
        result = chatty_spacy_service.chatbot(
            request.app.get('nlp'),
            request.app.get('doc_x'),
            request.app.get('doc_y'),
            request.app.get('intent_data'),
            message
        )

        return {
            'response': result
        }
