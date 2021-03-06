# -*- coding: utf-8 -*-

from .jsonrpc import validate_jsonrpc_request
from .jussi import add_jussi_request_id
from .jussi import finalize_jussi_response
from .caching import get_response
from .caching import cache_response


def setup_middlewares(app):
    logger = app.config.logger
    logger.info('before_server_start -> setup_middlewares')

    # request middleware
    app.request_middleware.append(add_jussi_request_id)
    app.request_middleware.append(validate_jsonrpc_request)
    app.request_middleware.append(get_response)

    # response middlware
    app.response_middleware.append(finalize_jussi_response)
    app.response_middleware.append(cache_response)

    logger.info(f'configured request middlewares:{app.request_middleware}')
    logger.info(f'configured response middlewares:{app.response_middleware}')
    return app
