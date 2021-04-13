from aiohttp import web
from chatty import routes
from chatty.orchestration.chattyOrchestration import ChattyOrchestration


@routes.get('/message')
async def message(request):
    http_status = 200
    message_orchestration = ChattyOrchestration()
    result = await message_orchestration.message(request)
    return web.json_response(data=result, status=http_status)


