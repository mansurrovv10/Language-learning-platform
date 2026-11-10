from dataclasses import dataclass

import httpx


@dataclass
class AIProviderResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class AIUnsafeError(ValueError):
    pass


class OpenAIResponsesProvider:
    def __init__(self, api_key: str, model: str, timeout: float = 15.0,
                 transport=None):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.transport = transport

    @staticmethod
    def _output_text(data: dict) -> str:
        if isinstance(data.get("output_text"),str):
            return data["output_text"]
        return "".join(
            content.get("text","")
            for output in data.get("output",[])
            for content in output.get("content",[])
            if content.get("type") == "output_text")

    async def _moderate(self,client,text,code):
        response = await client.post("/v1/moderations",json={
            "model":"omni-moderation-latest","input":text})
        response.raise_for_status()
        if response.json()["results"][0]["flagged"]:
            raise AIUnsafeError(code)

    async def generate(self, *, instructions, input_text, safety_identifier,
                       max_output_tokens, structured=False):
        headers = {"Authorization":f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url="https://api.openai.com",
                timeout=self.timeout,headers=headers,transport=self.transport) as client:
            await self._moderate(client,input_text,"AI_UNSAFE_INPUT")
            payload = {
                "model":self.model,"instructions":instructions,"input":input_text,
                "store":False,"max_output_tokens":max_output_tokens,
                "safety_identifier":safety_identifier}
            if structured:
                payload["text"]={"format":{
                    "type":"json_schema","name":"evaluation","strict":True,
                    "schema":{"type":"object","additionalProperties":False,
                        "properties":{"accepted":{"type":"boolean"},
                            "score":{"type":"number","minimum":0,"maximum":1},
                            "feedback":{"type":"string"}},
                        "required":["accepted","score","feedback"]}}}
            response=await client.post("/v1/responses",json=payload)
            response.raise_for_status()
            data = response.json()
            text = self._output_text(data)
            await self._moderate(client,text,"AI_UNSAFE_OUTPUT")
            usage = data.get("usage",{})
            return AIProviderResult(text=text,input_tokens=usage.get("input_tokens",0),
                                    output_tokens=usage.get("output_tokens",0))
