import json
from typing import Dict, Any
from chatty.database.chatty_db import ChattyDatabase


class UserService:

    def __init__(self, conn):
        self.chatty_db = ChattyDatabase(conn=conn)

    async def create_user_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        return self.chatty_db.upsert_user_session(
            session_id, json.dumps(session_data)
        )

    async def get_user_session(self, session_id: str) -> Dict[str, Any]:
        user_session = self.chatty_db.get_user_session(session_id)
        return json.loads(user_session) if user_session else {}
