import asyncio

from interact.base import Cascade, Message, handler
from interact.handlers import OpenAiLLM
from dotenv import load_dotenv

load_dotenv()


@handler
async def company_name_prompt(msg: Message, csd: Cascade) -> str:
    csd.vars["product"] = msg.primary
    return (
        f"What would be an appropriate name for a business specializing in {msg.primary}?"
        "Only mention the company name and nothing else."
    )


@handler
async def company_tagline_prompt(msg: Message, csd: Cascade) -> str:
    return (
        f"What would be an appropriate tagline for a business specializing in {csd.vars['product']}"
        f" and with company name {msg.primary}?\nFormat your output in the following"
        f" format:\n{msg.primary}: <tagline>"
    )


name_and_tagline_generator = (
    company_name_prompt >> OpenAiLLM() >> company_tagline_prompt >> OpenAiLLM()
)

print(asyncio.run(name_and_tagline_generator.start("socks")).last_msg)