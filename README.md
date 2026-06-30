# SPOT Generative AI Comms

A proof of concept that adds a voice-based conversational AI to a Boston Dynamics SPOT robot, similar to ChatGPT's voice mode. The system listens through a microphone, transcribes speech, generates a spoken reply, and plays it back, using Grok for the language model and ElevenLabs for speech-to-text and text-to-speech. It is built to talk with colleagues at a transportation and infrastructure agency about what SPOT can offer — its live LiDAR scanning capability and other use cases being explored. This PoC runs on a regular laptop with a USB mic and speakers before being moved onto the robot itself.

## How It Works

The system has two states. While **idle** it only listens for the activation phrase; once **active** it runs the full voice pipeline. You can switch states by voice (`"start spot"` / `"goodbye spot"`) or manually by pressing **Enter**.

## Setup

1. Clone the repo and enter the folder:
   ```bash
   git clone <repo-url>
   cd spot-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv

   # Mac/Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project folder with your API keys (see `.env.example`):
   ```
   XAI_API_KEY=your-xai-key-here
   ELEVENLABS_API_KEY=your-elevenlabs-key-here
   ```

## Running

```bash
# Mac/Linux (keyboard library needs root)
sudo python main.py

# Windows
python main.py
```

Once running, say **"start spot"** or press **Enter** to activate, then start talking. Say **"goodbye spot"** or press **Enter** again to deactivate. Press **Ctrl+C** to quit.