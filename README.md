# Multi-Agent AI Characters
Web app that allows 3 AI agents (using OpenAI, Claude, or Gemini) and a human to talk to each other.  
Written by DougDoug. Feel free to use this for whatever you want! Credit is appreciated but not required.  

This is uploaded for educational purposes. Unfortunately I don't have time to offer individual support or review pull requests, but ChatGPT or Claude can be very helpful if you are running into issues.

## SETUP
1) This was written in Python 3.9.2. Install page here: https://www.python.org/downloads/release/python-392/

2) Run `pip install -r requirements.txt` to install all modules. This will install dependencies for OpenAI, Anthropic Claude, Google Gemini, ElevenLabs, Flask, and more.

3) You will need API keys for the LLMs and TTS services you want to use. Set these as environment variables:
   - `OPENAI_API_KEY` (for OpenAI GPT-4o)
   - `ANTHROPIC_API_KEY` (for Claude)
   - `GOOGLE_API_KEY` (for Gemini)
   - `ELEVENLABS_API_KEY` (for ElevenLabs TTS)

4) This app uses the GPT-4o model from OpenAI by default. As of Sep 2024, you need to pay $5 to OpenAI to access the GPT-4o API. See: https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4-gpt-4-turbo-gpt-4o-and-gpt-4o-mini

5) ElevenLabs is used for AI voices. After creating voices on the ElevenLabs website, open `multi_agent_gpt.py` and ensure the correct voice names are passed to each agent.

6) This app uses the open source Whisper model from OpenAI for transcribing audio into text. Ideally, you have an Nvidia GPU for best performance. Whisper is used to transcribe the user's microphone and generate subtitles for agent speech. If you have issues with Whisper, you can use other audio-to-text services.

7) The app runs a Flask web server and displays the agents' dialogue using HTML and JavaScript. By default, it runs on `127.0.0.1:5151`, but you can change this in `multi_agent_gpt.py`.

8) Optionally, you can use OBS Websockets and the Move OBS plugin to animate images while agents talk. See the OBS section below for details.

## Using the App

1. Edit `ai_prompts.py` to design each agent's personality and conversation purpose.
2. Run `multi_agent_gpt.py`.
3. Use the web UI at `127.0.0.1:5151` to view agent dialogue and select LLMs for each agent.
4. Use keyboard shortcuts:
   - **Numpad7**: Start recording your microphone. **Numpad8**: Stop recording. Your speech is transcribed and added to all agents' chat histories, then a random agent is activated.
   - **Numpad1/2/3**: Activate Agent 1, 2, or 3, respectively. The agent will respond and then activate another agent (unless paused).
   - **F4**: Pause all agents (no new activations until unpaused).

## Multi-LLM Support

This app supports three LLM providers:
- **OpenAI** (GPT-4o, etc.)
- **Anthropic Claude** (e.g., Claude 3 Opus)
- **Google Gemini** (e.g., Gemini 1.5 Pro)

### Dynamic LLM Selection
- Each agent can use a different LLM provider and model.
- Use the dropdowns in the web UI to select the provider and model for each agent at any time. Click "Apply" to update the agent's LLM.
- The backend will switch the agent to the selected provider/model immediately.

### Provider Notes
- **Image analysis** is only supported for OpenAI GPT-4o.
- Claude and Gemini do not support image input/output in this app version.
- Token counting is most accurate for OpenAI; for others, it is estimated.

### Adding More Models
- You can add more models to the dropdowns in `index.html` if you have access to them via your API keys.

## OBS Integration (Optional)
- To animate images in OBS while agents talk, use OBS Websockets and the Move OBS plugin.
- See the original instructions above for setup details.

## Troubleshooting
- **Missing API Key**: If an agent fails to respond, check that the correct API key is set as an environment variable and that your account has access to the selected model.
- **Dependency Errors**: Ensure all dependencies in `requirements.txt` are installed. If you only want to use one provider, you can skip installing the others, but the UI will still show all options.
- **Whisper/Audio Issues**: If Whisper is slow, ensure you have installed the CUDA version of torch for GPU acceleration.
- **OBS Issues**: Make sure OBS is running and Websockets are enabled if you use the animation features.

## Miscellaneous Notes
- All agents automatically store their chat history in backup `.txt` files. To reset the conversation, delete these files.
- To display agent dialogue in OBS, add a browser source with the URL `127.0.0.1:5151`.
