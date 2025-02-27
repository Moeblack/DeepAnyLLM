"""基础客户端类,定义通用接口"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

import aiohttp
from aiohttp.client_exceptions import ClientError, ServerTimeoutError

import asyncio

from app.utils.logger import logger


class BaseClient(ABC):
    """基础客户端类"""

    # 默认超时设置(秒)
    # total: 总超时时间
    # connect: 连接超时时间
    # sock_read: 读取超时时间
    # TODO: 默认时间的设置涉及到模型推理速度，需要根据实际情况进行调整
    DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=600, connect=10, sock_read=500)

    def __init__(
        self,
        api_key: str,
        api_url: str,
        timeout: Optional[aiohttp.ClientTimeout] = None,
    ):
        """初始化基础客户端

        Args:
            api_key: API密钥
            api_url: API地址
            timeout: 请求超时设置,None则使用默认值
        """
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout or self.DEFAULT_TIMEOUT

    async def _make_request(
        self, headers: dict, data: dict, timeout: Optional[aiohttp.ClientTimeout] = None,
        cancel_event: Optional[asyncio.Event] = None
    ) -> AsyncGenerator[bytes, None]:
        """Send request and handle response with cancellation support

        Args:
            headers: Request headers
            data: Request data
            timeout: Current request timeout setting, None uses instance default
            cancel_event: Event to signal cancellation

        Yields:
            bytes: Raw response data

        Raises:
            aiohttp.ClientError: Client error
            ServerTimeoutError: Server timeout
            Exception: Other exceptions
        """
        request_timeout = timeout or self.timeout

        try:
            connector = aiohttp.TCPConnector(limit=100, force_close=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    self.api_url, headers=headers, json=data, timeout=request_timeout
                ) as response:
                    # Check response status
                    if not response.ok:
                        error_text = await response.text()
                        error_msg = f"API request failed: Status code {response.status}, Error: {error_text}"
                        logger.error(error_msg)
                        raise ClientError(error_msg)

                    # Stream response content with cancellation check
                    async for chunk in response.content.iter_any():
                        if cancel_event and cancel_event.is_set():
                            logger.info("Request cancelled, stopping stream")
                            break
                            
                        if chunk:  # Filter empty chunks
                            yield chunk

        except ServerTimeoutError as e:
            error_msg = f"Request timeout: {str(e)}"
            logger.error(error_msg)
            raise

        except ClientError as e:
            error_msg = f"Client error: {str(e)}"
            logger.error(error_msg)
            raise

        except Exception as e:
            error_msg = f"Request processing exception: {str(e)}"
            logger.error(error_msg)
            raise

    @abstractmethod
    async def stream_chat(
        self, messages: list, model: str
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话，由子类实现

        Args:
            messages: 消息列表
            model: 模型名称

        Yields:
            tuple[str, str]: (内容类型, 内容)
        """
        pass
