import asyncio

from dotenv import load_dotenv

from interact import Handler, HandlerChain, Message
from interact.handlers import OpenAiLLM

load_dotenv()  # assuming that the OpenAI api key is set in the environment


class CompanyNamePrompt(Handler):
    role = "CompanyNameGenerator"
    prompt = (
        "What would be an appropriate name for a business specializing in {product}?"
    )

    async def process(self, msg: Message, chain: HandlerChain) -> str:
        new_msg = self.prompt.format(product=msg.primary)
        chain.variables["product"] = msg.primary
        return new_msg


class CompanyTaglinePrompt(Handler):
    role = "CompanyTaglineGenerator"
    prompt = (
        "What would be an appropriate tagline for a business specializing in {product}"
        " and with company name {company_name}?\nFormat your output in the following"
        " format:\n<company_name>: <tagline>"
    )

    async def process(self, msg: Message, chain: HandlerChain) -> str:
        new_msg = self.prompt.format(
            company_name=msg.primary, product=chain.variables["product"]
        )
        return new_msg


def main():
    name_and_tagline_generator = (
        CompanyNamePrompt() >> OpenAiLLM() >> CompanyTaglinePrompt() >> OpenAiLLM()
    )

    res, history = asyncio.run(name_and_tagline_generator("bike", return_history=True))
    for msg in history:
        print(msg.sender)
        print(msg)
    print(res)
    # >> The Sock Spot: Step into Comfort


if __name__ == "__main__":
    main()
