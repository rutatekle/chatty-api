from aiohttp import web
from aiohttp_session import setup, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
import base64
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

    # secret_key must be 32 url-safe base64-encoded bytes
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))

    port = 8085
    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
