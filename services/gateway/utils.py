import os
import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)

PATHWAY_URL = os.getenv("PATHWAY_URL", "http://localhost:8080/")

async def _forward_with_retry(client: httpx.AsyncClient, url: str, payload: dict) -> None:
    max_retries = 3
    backoff_factor = 0.5
    for attempt in range(1, max_retries + 1):
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return  # Success
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed connecting to Pathway at {url}: {e}"
            )
            if attempt == max_retries:
                logger.error(
                    f"Failed to connect to Pathway at {url} after {max_retries} attempts."
                )
            else:
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.error(f"Unexpected error when forwarding to Pathway: {e}")
            break
