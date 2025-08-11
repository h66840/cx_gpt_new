import os
import base64
import json
import re
from typing import Dict, Any, AsyncGenerator
import dashscope
from openai import OpenAI
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class AIClient:
    def __init__(self):
        self.aliyun_api_key = os.getenv("ALIYUN_API_KEY")
        self.aliyun_base_url = os.getenv("ALIYUN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.qwen_vl_model = "qwen-vl-max"
        
        if not self.aliyun_api_key:
            raise ValueError("ALIYUN_API_KEY is not set in environment variables.")
            
        dashscope.api_key = self.aliyun_api_key
        self.openai_client = OpenAI(api_key=self.aliyun_api_key, base_url=self.aliyun_base_url)

    async def analyze_image(self, image_bytes: bytes, prompt: str) -> Dict[str, Any]:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"

        messages = [{"role": "user", "content": [{"image": image_url}, {"text": prompt}]}]

        try:
            response = dashscope.MultiModalConversation.call(
                model=self.qwen_vl_model,
                messages=messages,
                temperature=0.0,
            )
            if response.status_code != 200:
                raise Exception(f"AI API call failed: {response.message}")
            
            content = response.output.choices[0].message.content
            response_text = content[0]["text"] if isinstance(content, list) else content
            
            match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text)
            json_text = match.group(1) if match else response_text
            
            return json.loads(json_text)
            
        except Exception as e:
            raise Exception(f"Failed during AI analysis: {e}")

    async def analyze_image_stream(self, image_bytes: bytes, prompt: str) -> AsyncGenerator[str, None]:
        """
        Analyzes an image from bytes and streams the response.
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"

        try:
            stream = self.openai_client.chat.completions.create(
                model=self.qwen_vl_model,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': image_url}}
                    ]
                }],
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error during AI analysis stream: {e}"

    async def describe_image_stream(self, image_url: str, prompt: str) -> AsyncGenerator[str, None]:
        if not image_url.startswith(('http://', 'https://')):
            yield "Error: Invalid image_url format."
            return

        try:
            stream = self.openai_client.chat.completions.create(
                model=self.qwen_vl_model,
                messages=[{'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {'type': 'image_url', 'image_url': {'url': image_url}}]
                }],
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {e}"

# Singleton instance
ai_client = AIClient()
