from aiohttp import web
from chatty import routes
from aiohttp_middlewares import cors_middleware
import chatty.handlers
from chatty.services.chatty_spacy_service import ChattySpacyService
from chatty.database.chatty_db import ChattyDatabase


def main():
    app = web.Application(
        middlewares=[cors_middleware(allow_all=True)]
    )
    app.add_routes(routes)

    app['nlp'] = ChattySpacyService.load_nlp()
    doc_x, doc_y, intent_data = ChattySpacyService.get_docx_and_docy(app['nlp'])
    app['doc_x'] = doc_x
    app['doc_y'] = doc_y
    app['conn'] = ChattyDatabase.create_connection(r'data/restaurant.db')
    app['intent_data'] = intent_data

    port = 8085
    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
