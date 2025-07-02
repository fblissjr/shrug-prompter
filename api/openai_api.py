# In shrug-prompter/api/openai_api.py
import aiohttp
import asyncio

async def send_request_openai(messages, api_key, base_url, llm_model, max_tokens, temperature, top_p, mask=None):
    """
    Sends a request to an OpenAI-compatible API endpoint (including edge-llm).

    Args:
        messages (list): The list of messages for the chat completion payload.
        api_key (str): The API key for authorization.
        base_url (str): The base URL of the API endpoint.
        llm_model (str): The model name to use.
        max_tokens (int): The maximum number of tokens to generate.
        temperature (float): The sampling temperature.
        top_p (float): The nucleus sampling probability.
        mask (str, optional): A Base64-encoded mask string (custom for some servers).

    Returns:
        A dictionary containing the API response or an error message.
    """
    endpoint = f"{base_url.strip('/')}/v1/chat/completions"

    # Prepare headers
    headers = {"Content-Type": "application/json"}

    # Only add Authorization header if API key is provided
    # (local servers like edge-llm might not require it)
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key}"

    # Prepare payload
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False
    }

    # Add model if provided (required for most APIs)
    if llm_model and llm_model.strip():
        # Clean up model name (remove vision indicators)
        clean_model = llm_model.replace(" (Vision)", "").strip()
        payload["model"] = clean_model

    # Add mask if provided (custom extension)
    if mask:
        payload["mask"] = mask

    # Debug logging
    print(f"Sending request to: {endpoint}")
    print(f"Model: {payload.get('model', 'not specified')}")
    print(f"Messages: {len(messages)} message(s)")

    try:
        # Create session with longer timeout for local inference
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for local LLM inference

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(endpoint, json=payload, headers=headers) as response:

                # Get response text for debugging
                response_text = await response.text()

                if response.status == 200:
                    try:
                        response_json = await response.json()
                        print(f"SUCCESS: Received response with {len(response_json.get('choices', []))} choice(s)")
                        return response_json
                    except Exception as json_error:
                        print(f"ERROR: Could not parse JSON response: {json_error}")
                        print(f"Raw response: {response_text[:500]}")
                        return {"error": {"message": f"Invalid JSON response: {json_error}"}}
                else:
                    print(f"ERROR: HTTP {response.status}: {response_text}")
                    return {"error": {"message": f"HTTP {response.status}: {response_text}"}}

    except asyncio.TimeoutError:
        print("ERROR: Request timed out")
        return {"error": {"message": "Request timed out - inference took too long"}}
    except aiohttp.ClientConnectorError as e:
        print(f"ERROR: Could not connect to server: {e}")
        return {"error": {"message": f"Connection failed: {str(e)}"}}
    except aiohttp.ClientError as e:
        print(f"ERROR: Client error: {e}")
        return {"error": {"message": f"Client error: {str(e)}"}}
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return {"error": {"message": f"Unexpected error: {str(e)}"}}
