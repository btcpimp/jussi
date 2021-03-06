# -*- coding: utf-8 -*-
import logging
from typing import Optional

import cytoolz

from ..typedefs import BatchJsonRpcRequest
from ..typedefs import CachedBatchResponse
from ..typedefs import CachedSingleResponse
from ..typedefs import SingleJsonRpcRequest
from ..upstream.urn import urn
from .method_settings import TTL
from .method_settings import TTLS

logger = logging.getLogger(__name__)


def jsonrpc_cache_key(single_jsonrpc_request: SingleJsonRpcRequest) -> str:
    return urn(single_jsonrpc_request)


def ttl_from_jsonrpc_request(single_jsonrpc_request: SingleJsonRpcRequest,
                             last_irreversible_block_num: int=0,
                             jsonrpc_response: dict=None) -> TTL:
    urn = jsonrpc_cache_key(single_jsonrpc_request=single_jsonrpc_request)
    ttl = ttl_from_urn(urn)
    if ttl == TTL.NO_EXPIRE_IF_IRREVERSIBLE:
        ttl = irreversible_ttl(jsonrpc_response, last_irreversible_block_num)
    if isinstance(ttl, TTL):
        ttl = ttl.value
    return ttl


def ttl_from_urn(urn: str) -> TTL:
    _, ttl = TTLS.longest_prefix(urn)
    logger.debug(f'ttl from urn:{urn} ttl:{ttl}')
    return ttl


def irreversible_ttl(jsonrpc_response: dict=None,
                     last_irreversible_block_num: int=0) -> TTL:
    if not jsonrpc_response:
        logger.debug(
            'bad.missing block num in response, skipping cache')
        return TTL.NO_CACHE
    if not last_irreversible_block_num:
        logger.debug('bad/missing last_irrersible_block_num, skipping cache')
        return TTL.NO_CACHE
    try:
        jrpc_block_num = block_num_from_jsonrpc_response(jsonrpc_response)
        if jrpc_block_num <= last_irreversible_block_num:
            return TTL.NO_EXPIRE
    except Exception as e:
        logger.info('Unable to cache using last irreversible block: %s', e)
    logger.debug('skipping cache for block_num > last_irreversible')
    return TTL.NO_CACHE


def block_num_from_jsonrpc_response(
        jsonrpc_response: SingleJsonRpcRequest=None) -> int:
    # pylint: disable=no-member
    # for get_block
    block_id = cytoolz.get_in(['result', 'block_id'], jsonrpc_response)
    if block_id:
        return block_num_from_id(block_id)

    # for get_block_header
    previous = cytoolz.get_in(['result', 'previous'], jsonrpc_response)
    return block_num_from_id(previous) + 1


def block_num_from_id(block_hash: str) -> int:
    """return the first 4 bytes (8 hex digits) of the block ID (the block_num)
    """
    return int(str(block_hash)[:8], base=16)


def merge_cached_response(request: SingleJsonRpcRequest,
                          cached_response: CachedSingleResponse,
                          ) -> Optional[SingleJsonRpcRequest]:
    if not cached_response:
        return None
    new_response = {'jsonrpc': '2.0', 'result': cached_response['result']}
    if 'id' in request:
        new_response['id'] = request['id']
    return new_response


def merge_cached_responses(request: BatchJsonRpcRequest,
                           cached_responses: CachedBatchResponse) -> CachedBatchResponse:
    return [merge_cached_response(req, resp) for req, resp in zip(
        request, cached_responses)]
