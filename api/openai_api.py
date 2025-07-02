# In shrug-prompter/api/openai_api.py
import aiohttp

async def send_request_openai(messages, api_key, base_url, max_tokens, temperature, top_p, mask=None):
    """
    Sends a request to an OpenAI-compatible API endpoint.

    Args:
        messages (list): The list of messages for the chat completion payload.
        api_key (str): The API key for authorization.
        base_url (str): The base URL of the API endpoint.
        max_tokens (int): The maximum number of tokens to generate.
        temperature (float): The sampling temperature.
        top_p (float): The nucleus sampling probability.
        mask (str, optional): A Base64-encoded mask string (custom for some servers).

    Returns:
        A dictionary containing the API response or an error message.
    """
    endpoint = f"{base_url.strip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False
    }

    if mask:
        payload["mask"] = mask

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers, timeout=240) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        print(f"ERROR: OpenAI API request failed: {e}")
        return {"error": {"message": str(e)}}
