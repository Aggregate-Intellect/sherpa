import time
import uuid
from typing import Any, Callable, Dict, Optional

from httpx import URL

from posthog.client import Client as PostHogClient


def get_model_params(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts model parameters from the kwargs dictionary.
    """
    model_params = {}
    for param in [
        "temperature",
        "max_tokens",  # Deprecated field
        "max_completion_tokens",
        "top_p",
        "frequency_penalty",
        "presence_penalty",
        "n",
        "stop",
        "stream",  # OpenAI-specific field
        "streaming",  # Anthropic-specific field
    ]:
        if param in kwargs and kwargs[param] is not None:
            model_params[param] = kwargs[param]
    return model_params


def get_usage(response, provider: str) -> Dict[str, Any]:
    if provider == "anthropic":
        return {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
    elif provider == "openai":
        return {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }
    return {
        "input_tokens": 0,
        "output_tokens": 0,
    }


def format_response(response, provider: str):
    """
    Format a regular (non-streaming) response.
    """
    output = []
    if response is None:
        return output
    if provider == "anthropic":
        return format_response_anthropic(response)
    elif provider == "openai":
        return format_response_openai(response)
    return output


def format_response_anthropic(response):
    output = []
    for choice in response.content:
        if choice.text:
            output.append(
                {
                    "role": "assistant",
                    "content": choice.text,
                }
            )
    return output


def format_response_openai(response):
    output = []
    for choice in response.choices:
        if choice.message.content:
            output.append(
                {
                    "content": choice.message.content,
                    "role": choice.message.role,
                }
            )
    return output


def merge_system_prompt(kwargs: Dict[str, Any], provider: str):
    if provider != "anthropic":
        return kwargs.get("messages")
    messages = kwargs.get("messages") or []
    if kwargs.get("system") is None:
        return messages
    return [{"role": "system", "content": kwargs.get("system")}] + messages


def call_llm_and_track_usage(
    posthog_distinct_id: Optional[str],
    ph_client: PostHogClient,
    provider: str,
    posthog_trace_id: Optional[str],
    posthog_properties: Optional[Dict[str, Any]],
    posthog_privacy_mode: bool,
    posthog_groups: Optional[Dict[str, Any]],
    base_url: URL,
    call_method: Callable[..., Any],
    **kwargs: Any,
) -> Any:
    """
    Common usage-tracking logic for both sync and async calls.
    call_method: the llm call method (e.g. openai.chat.completions.create)
    """
    start_time = time.time()
    response = None
    error = None
    http_status = 200
    usage: Dict[str, Any] = {}
    error_params: Dict[str, any] = {}

    try:
        response = call_method(**kwargs)
    except Exception as exc:
        error = exc
        http_status = getattr(exc, "status_code", 0)  # default to 0 becuase its likely an SDK error
        error_params = {
            "$ai_is_error": True,
            "$ai_error": exc.__str__(),
        }
    finally:
        end_time = time.time()
        latency = end_time - start_time

        if posthog_trace_id is None:
            posthog_trace_id = uuid.uuid4()

        if response and hasattr(response, "usage"):
            usage = get_usage(response, provider)

        messages = merge_system_prompt(kwargs, provider)

        event_properties = {
            "$ai_provider": provider,
            "$ai_model": kwargs.get("model"),
            "$ai_model_parameters": get_model_params(kwargs),
            "$ai_input": with_privacy_mode(ph_client, posthog_privacy_mode, messages),
            "$ai_output_choices": with_privacy_mode(
                ph_client, posthog_privacy_mode, format_response(response, provider)
            ),
            "$ai_http_status": http_status,
            "$ai_input_tokens": usage.get("input_tokens", 0),
            "$ai_output_tokens": usage.get("output_tokens", 0),
            "$ai_latency": latency,
            "$ai_trace_id": posthog_trace_id,
            "$ai_base_url": str(base_url),
            **(posthog_properties or {}),
            **(error_params or {}),
        }

        if posthog_distinct_id is None:
            event_properties["$process_person_profile"] = False

        # send the event to posthog
        if hasattr(ph_client, "capture") and callable(ph_client.capture):
            ph_client.capture(
                distinct_id=posthog_distinct_id or posthog_trace_id,
                event="$ai_generation",
                properties=event_properties,
                groups=posthog_groups,
            )

    if error:
        raise error

    return response


async def call_llm_and_track_usage_async(
    posthog_distinct_id: Optional[str],
    ph_client: PostHogClient,
    provider: str,
    posthog_trace_id: Optional[str],
    posthog_properties: Optional[Dict[str, Any]],
    posthog_privacy_mode: bool,
    posthog_groups: Optional[Dict[str, Any]],
    base_url: URL,
    call_async_method: Callable[..., Any],
    **kwargs: Any,
) -> Any:
    start_time = time.time()
    response = None
    error = None
    http_status = 200
    usage: Dict[str, Any] = {}
    error_params: Dict[str, any] = {}

    try:
        response = await call_async_method(**kwargs)
    except Exception as exc:
        error = exc
        http_status = getattr(exc, "status_code", 0)  # default to 0 because its likely an SDK error
        error_params = {
            "$ai_is_error": True,
            "$ai_error": exc.__str__(),
        }
    finally:
        end_time = time.time()
        latency = end_time - start_time

        if posthog_trace_id is None:
            posthog_trace_id = uuid.uuid4()

        if response and hasattr(response, "usage"):
            usage = get_usage(response, provider)

        messages = merge_system_prompt(kwargs, provider)

        event_properties = {
            "$ai_provider": provider,
            "$ai_model": kwargs.get("model"),
            "$ai_model_parameters": get_model_params(kwargs),
            "$ai_input": with_privacy_mode(ph_client, posthog_privacy_mode, messages),
            "$ai_output_choices": with_privacy_mode(
                ph_client, posthog_privacy_mode, format_response(response, provider)
            ),
            "$ai_http_status": http_status,
            "$ai_input_tokens": usage.get("input_tokens", 0),
            "$ai_output_tokens": usage.get("output_tokens", 0),
            "$ai_latency": latency,
            "$ai_trace_id": posthog_trace_id,
            "$ai_base_url": str(base_url),
            **(posthog_properties or {}),
            **(error_params or {}),
        }

        if posthog_distinct_id is None:
            event_properties["$process_person_profile"] = False

        # send the event to posthog
        if hasattr(ph_client, "capture") and callable(ph_client.capture):
            ph_client.capture(
                distinct_id=posthog_distinct_id or posthog_trace_id,
                event="$ai_generation",
                properties=event_properties,
                groups=posthog_groups,
            )

    if error:
        raise error

    return response


def with_privacy_mode(ph_client: PostHogClient, privacy_mode: bool, value: Any):
    if ph_client.privacy_mode or privacy_mode:
        return None
    return value
