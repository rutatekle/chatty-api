from aiohttp import web
import json
from aiohttp_session import get_session
import aiohttp
from chatty import routes
from chatty.services.user_service import UserService
from chatty.orchestration.chattyOrchestration import ChattyOrchestration


@routes.get('/message')
async def message(request):
    session_id = request.headers.get('AUTHORIZATION')
    if not session_id:
        return web.json_response(
            data={
                'error': 'Please pass AUTHORIZATION valid header. Please make sure you have PHPSESSID'
                         ' cookie set in your browser'}, status=403
        )

    user_service = UserService(request.app.get('conn'))
    session = await get_session(request)
    session['session_data'] = await user_service.get_user_session(session_id)

    message_orchestration = ChattyOrchestration()
    result = await message_orchestration.message(request)

    await user_service.create_user_session(session_id, session.get('session_data', ''))
    return web.json_response(data=result, status=200)


