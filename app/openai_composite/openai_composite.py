import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, List

from fastapi import Request  # IMPORTANT: Import Request here

from app.clients import DeepSeekClient
from app.clients.openai_compatible_client import OpenAICompatibleClient  # Corrected import
from app.utils.logger import logger

class OpenAICompatibleComposite:
    """处理 DeepSeek 和其他 OpenAI 兼容模型的流式输出衔接"""

    def __init__(
        self,
        deepseek_api_key: str,
        openai_api_key: str,
        deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions",
        openai_api_url: str = "",  # 将由具体实现提供
        is_origin_reasoning: bool = True,
    ):
        """初始化 API 客户端"""
        self.deepseek_client = DeepSeekClient(deepseek_api_key, deepseek_api_url)
        self.openai_client = OpenAICompatibleClient(openai_api_key, openai_api_url)
        self.is_origin_reasoning = is_origin_reasoning

    async def chat_completions_with_stream(
        self,
        request: Request,  # Correctly added Request parameter
        messages: List[Dict[str, str]],
        model_arg: tuple[float, float, float, float],
        deepseek_model: str = "deepseek-reasoner",
        target_model: str = "",
    ) -> AsyncGenerator[bytes, None]:
        """处理完整的流式输出过程，并处理客户端断开连接

        Args:
            request: FastAPI Request 对象，用于检查客户端连接状态
            messages: 初始消息列表
            model_arg: 模型参数 (temperature, top_p, presence_penalty, frequency_penalty)
            deepseek_model: DeepSeek 模型名称
            target_model: 目标 OpenAI 兼容模型名称

        Yields:
            字节流数据 (OpenAI 格式的 chunk)
        """

        # Generate a unique chat ID and creation timestamp
        chat_id = f"chatcmpl-{hex(int(time.time() * 1000))[2:]}"
        created_time = int(time.time())

        # Queues for collecting output and DeepSeek reasoning
        output_queue = asyncio.Queue()
        reasoning_queue = asyncio.Queue()

        # Store accumulated reasoning content from DeepSeek
        reasoning_content = []

        # Cancellation event for handling client disconnections
        cancel_event = asyncio.Event()

        async def check_client_connection():
            """Task to continuously monitor client connection."""
            while not cancel_event.is_set():
                if await request.is_disconnected():
                    logger.info("Client disconnected, setting cancel event")
                    cancel_event.set()
                    return  # Exit the monitoring task
                await asyncio.sleep(0.1)  # Check every 100ms

        async def process_deepseek():
            """Task to handle DeepSeek API calls and reasoning extraction."""
            logger.info(f"Starting DeepSeek stream processing with model: {deepseek_model}")
            try:
                async for content_type, content in self.deepseek_client.stream_chat(
                    messages, deepseek_model, self.is_origin_reasoning
                ):
                    if cancel_event.is_set():
                        logger.info("Cancellation detected, stopping DeepSeek")
                        break  # Exit DeepSeek processing

                    if content_type == "reasoning":
                        reasoning_content.append(content)
                        response = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": deepseek_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "reasoning_content": content,
                                        "content": "",  # No regular content yet
                                    },
                                }
                            ],
                        }
                        await output_queue.put(
                            f"data: {json.dumps(response)}\n\n".encode("utf-8")
                        )

                    elif content_type == "content":
                        logger.info(
                            f"DeepSeek reasoning complete, collected reasoning length: {len(''.join(reasoning_content))}"
                        )
                        await reasoning_queue.put("".join(reasoning_content))
                        break  # Reasoning is complete, stop DeepSeek stream

            except Exception as e:
                logger.error(f"Error processing DeepSeek stream: {e}")
                await reasoning_queue.put("")  # Signal failure

            finally:
                if not cancel_event.is_set():  # Only put None if *not* cancelled
                    logger.info("DeepSeek task finished, marking end.")
                    await output_queue.put(None) # Signal completion

        async def process_openai():
            """Task to handle OpenAI-compatible API calls."""
            try:
                logger.info("Waiting for DeepSeek reasoning content...")
                reasoning = await reasoning_queue.get()
                logger.debug(
                    f"Received reasoning content, length: {len(reasoning) if reasoning else 0}"
                )

                if cancel_event.is_set():
                    logger.info("Cancellation detected, stopping OpenAI processing")
                    return

                if not reasoning:
                    logger.warning("No valid reasoning content, using default prompt")
                    reasoning = "Failed to retrieve reasoning content"

                # Construct OpenAI input messages
                openai_messages = messages.copy()
                combined_content = (
                    "Here's my another model's reasoning process:\n"
                    f"{reasoning}\n\n"
                    "Based on this reasoning, provide your response directly to me:"
                )

                # Check if the message list is empty
                if not openai_messages:
                    raise ValueError("Message list is empty, cannot process request")

                # Ensure the last message is from the user
                last_message = openai_messages[-1]
                if last_message.get("role", "") != "user":
                    raise ValueError("Last message is not from user, cannot process")

                # Modify the last message content
                original_content = last_message["content"]
                fixed_content = (
                    "Here's my original input:\n"
                    f"{original_content}\n\n{combined_content}"
                )
                last_message["content"] = fixed_content

                logger.info(f"Starting OpenAI compatible stream processing with model: {target_model}")

                async for role, content in self.openai_client.stream_chat(
                    messages=openai_messages,
                    model=target_model,
                ):
                    if cancel_event.is_set():
                        logger.info("Cancellation detected, stopping OpenAI output")
                        break

                    response = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": target_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": role, "content": content},
                            }
                        ],
                    }
                    await output_queue.put(
                        f"data: {json.dumps(response)}\n\n".encode("utf-8")
                    )
            except Exception as e:
                logger.error(f"Error processing OpenAI compatible stream: {e}")
            finally:
                if not cancel_event.is_set():
                    logger.info("OpenAI compatible task finished, marking end.")
                    await output_queue.put(None)  # Signal completion

        # Create and start tasks
        connection_task = asyncio.create_task(check_client_connection())
        deepseek_task = asyncio.create_task(process_deepseek())
        openai_task = asyncio.create_task(process_openai())

        tasks = [deepseek_task, openai_task, connection_task]

        try:
            # Wait for both DeepSeek and OpenAI tasks to complete (or cancellation)
            finished_tasks = 0
            while finished_tasks < 2 and not cancel_event.is_set():
                try:
                    item = await asyncio.wait_for(output_queue.get(), timeout=0.5)
                    if item is None:  # None indicates a task is complete
                        finished_tasks += 1
                    else:
                        yield item
                except asyncio.TimeoutError:
                    # Periodically check for disconnection, even if no data is ready
                    if cancel_event.is_set():
                        logger.info("Client disconnected during timeout, breaking loop")
                        break
                    continue #Continue checking

            # Send the final [DONE] message if not cancelled
            if not cancel_event.is_set():
                yield b"data: [DONE]\n\n"

        except GeneratorExit:
            logger.info("GeneratorExit caught: Client closed connection prematurely.")
            cancel_event.set()  # Signal cancellation

        finally:
            # Cancel all tasks to ensure proper cleanup
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for tasks to be cancelled. return_exceptions=True prevents
            # asyncio.gather from raising exceptions if tasks were cancelled.
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All tasks cleaned up.")

    async def chat_completions_without_stream(
        self,
        request: Request,
        messages: List[Dict[str, str]],
        model_arg: tuple[float, float, float, float],
        deepseek_model: str = "deepseek-reasoner",
        target_model: str = "",
    ) -> Dict[str, Any]:
        """处理非流式输出请求

        Args:
            messages: 初始消息列表
            model_arg: 模型参数
            deepseek_model: DeepSeek 模型名称
            target_model: 目标 OpenAI 兼容模型名称

        Returns:
            Dict[str, Any]: 完整的响应数据
        """
        full_response = {
            "id": f"chatcmpl-{hex(int(time.time() * 1000))[2:]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": target_model,
            "choices": [],
            "usage": {},
        }

        content_parts = []
        async for chunk in self.chat_completions_with_stream(
            request, messages, model_arg, deepseek_model, target_model
        ):
            if chunk != b"data: [DONE]\n\n":
                try:
                    response_data = json.loads(chunk.decode("utf-8")[6:])
                    if (
                        "choices" in response_data
                        and len(response_data["choices"]) > 0
                        and "delta" in response_data["choices"][0]
                    ):
                        delta = response_data["choices"][0]["delta"]
                        if "content" in delta and delta["content"]:
                            content_parts.append(delta["content"])
                except json.JSONDecodeError:
                    continue

        full_response["choices"] = [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "".join(content_parts)},
                "finish_reason": "stop",
            }
        ]

        return full_response
