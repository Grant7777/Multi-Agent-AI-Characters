import tiktoken
import os
from rich import print
import base64
import time
import json

# --- BEGIN REFACTOR ---
class LLMManager:
    def __init__(self, system_prompt=None, chat_history_backup=None, provider='openai', model=None):
        """
        provider: 'openai', 'claude', or 'gemini'
        model: model name for the provider (e.g., 'gpt-4o', 'claude-3-opus-20240229', 'gemini-1.5-pro')
        """
        self.provider = provider
        self.model = model or self._default_model_for_provider(provider)
        self.logging = True
        self.tiktoken_encoder = None
        self.chat_history = []
        self.chat_history_backup = chat_history_backup
        self._init_client()
        # Load chat history or system prompt
        if chat_history_backup and os.path.exists(chat_history_backup):
            with open(chat_history_backup, 'r') as file:
                self.chat_history = json.load(file)
        elif system_prompt:
            self.chat_history.append(system_prompt)

    def _default_model_for_provider(self, provider):
        if provider == 'openai':
            return 'gpt-4o'
        elif provider == 'claude':
            return 'claude-3-opus-20240229'
        elif provider == 'gemini':
            return 'gemini-1.5-pro'
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _init_client(self):
        if self.provider == 'openai':
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
            except ImportError:
                print("[red]ERROR: OpenAI client not available. Please install openai package.")
                self.client = None
        elif self.provider == 'claude':
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
            except ImportError:
                print("[red]ERROR: Claude client not available. Please install anthropic package.")
                self.client = None
        elif self.provider == 'gemini':
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
                self.client = genai
            except ImportError:
                print("[red]ERROR: Gemini client not available. Please install google-generativeai package.")
                self.client = None
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def set_provider(self, provider, model=None):
        self.provider = provider
        self.model = model or self._default_model_for_provider(provider)
        self._init_client()

    def save_chat_to_backup(self):
        if self.chat_history_backup:
            with open(self.chat_history_backup, 'w') as file:
                json.dump(self.chat_history, file)

    def num_tokens_from_messages(self, messages, model=None):
        model = model or self.model
        if self.provider == 'openai':
            try:
                if self.tiktoken_encoder is None:
                    import tiktoken
                    self.tiktoken_encoder = tiktoken.encoding_for_model(model)
                num_tokens = 0
                for message in messages:
                    num_tokens += 4
                    for key, value in message.items():
                        if key == 'role':
                            num_tokens += len(self.tiktoken_encoder.encode(value))
                        elif key == 'content':
                            if isinstance(value, str):
                                num_tokens += len(self.tiktoken_encoder.encode(value))
                                continue
                            for message_data in value:
                                for content_key, content_value in message_data.items():
                                    if content_key == 'type':
                                        num_tokens += len(self.tiktoken_encoder.encode(content_value))
                                    elif content_key == 'text':
                                        num_tokens += len(self.tiktoken_encoder.encode(content_value))
                                    elif content_key == "image_url":
                                        num_tokens += 1105
                num_tokens += 2
                return num_tokens
            except Exception:
                raise NotImplementedError(f"num_tokens_from_messages() is not implemented for model {model}.")
        else:
            # For Claude/Gemini, return a rough estimate (1 token ~= 4 chars)
            return sum(len(str(m)) // 4 for m in messages)

    def chat(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return
        if self.provider == 'openai':
            if self.client is None:
                print("[red]ERROR: OpenAI client not initialized.")
                return
            chat_question = [{"role": "user", "content": prompt}]
            if self.num_tokens_from_messages(chat_question) > 128000:
                print("The length of this chat question is too large for the GPT model")
                return
            print("[yellow]\nAsking OpenAI a question...")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=chat_question
            )
            answer = completion.choices[0].message.content
        elif self.provider == 'claude':
            if self.client is None:
                print("[red]ERROR: Claude client not initialized.")
                return
            print("[yellow]\nAsking Claude a question...")
            completion = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = completion.content[0].text if hasattr(completion.content[0], 'text') else completion.content[0]
        elif self.provider == 'gemini':
            if self.client is None:
                print("[red]ERROR: Gemini client not initialized.")
                return
            print("[yellow]\nAsking Gemini a question...")
            model = self.client.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            answer = response.text
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        if self.logging:
            print(f"[green]\n{answer}\n")
        return answer

    def analyze_image(self, prompt, image_path, local_image=True):
        if self.client is None:
            print("[red]ERROR: Image analysis is not available for this provider.")
            return None
        if self.provider == 'openai':
            # Use default prompt if one isn't provided
            if prompt is None:
                prompt = "Please give me a detailed description of this image."
            if local_image:
                try:
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                        url = f"data:image/jpeg;base64,{base64_image}"
                except:
                    print("[red]ERROR: COULD NOT BASE64 ENCODE THE IMAGE. PANIC!!")
                    return None
            else:
                url = image_path
            if self.logging:
                print("[yellow]\nAsking OpenAI to analyze image...")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": url,
                                    "detail": "high"
                                }
                            },
                        ],
                    },
                ],
                max_tokens=4096,
            )
            answer = completion.choices[0].message.content
            if self.logging:
                print(f"[green]\n{answer}\n")
            return answer
        else:
            print("[red]Image analysis is only supported for OpenAI GPT-4o at this time.")
            return None

    def chat_with_history(self, prompt="", image_path="", local_image=True):
        if prompt is not None and prompt != "":
            new_chat_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
            if image_path != "":
                if local_image:
                    try:
                        with open(image_path, "rb") as image_file:
                            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                            url = f"data:image/jpeg;base64,{base64_image}"
                    except:
                        print("[red]ERROR: COULD NOT BASE64 ENCODE THE IMAGE. PANIC!!")
                        return None
                else:
                    url = image_path
                new_image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "high"
                    }
                }
                new_chat_message["content"].append(new_image_content)
            self.chat_history.append(new_chat_message)
        # Check total token limit. Remove old messages as needed
        if self.logging:
            print(f"[coral]Chat History has a current token length of {self.num_tokens_from_messages(self.chat_history)}")
        while self.num_tokens_from_messages(self.chat_history) > 128000:
            self.chat_history.pop(1)
            if self.logging:
                print(f"Popped a message! New token length is: {self.num_tokens_from_messages(self.chat_history)}")
        if self.logging:
            print(f"[yellow]\nAsking {self.provider} a question...")
        if self.provider == 'openai':
            if self.client is None:
                print("[red]ERROR: OpenAI client not initialized.")
                return None
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history
            )
            role = completion.choices[0].message.role
            content = completion.choices[0].message.content
        elif self.provider == 'claude':
            if self.client is None:
                print("[red]ERROR: Claude client not initialized.")
                return None
            completion = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=self._claude_history_format(self.chat_history)
            )
            role = 'assistant'
            content = completion.content[0].text if hasattr(completion.content[0], 'text') else completion.content[0]
        elif self.provider == 'gemini':
            if self.client is None:
                print("[red]ERROR: Gemini client not initialized.")
                return None
            model = self.client.GenerativeModel(self.model)
            # Gemini does not support chat history in the same way; concatenate messages
            def get_gemini_text(m):
                if isinstance(m['content'], list) and m['content'] and isinstance(m['content'][0], dict) and 'text' in m['content'][0]:
                    return m['content'][0].get('text', '')
                return str(m['content'])
            history_text = '\n'.join([get_gemini_text(m) for m in self.chat_history if m['role'] == 'user'])
            response = model.generate_content(history_text)
            role = 'assistant'
            content = response.text
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        self.chat_history.append({"role": role, "content": content})
        self.save_chat_to_backup()
        if self.logging:
            print(f"[green]\n{content}\n")
        return content

    def _claude_history_format(self, chat_history):
        # Convert OpenAI-style history to Claude format
        claude_history = []
        for m in chat_history:
            if isinstance(m['content'], list):
                text = '\n'.join([c['text'] for c in m['content'] if 'text' in c])
            else:
                text = m['content']
            claude_history.append({"role": m['role'], "content": text})
        return claude_history

# --- END REFACTOR ---
    
