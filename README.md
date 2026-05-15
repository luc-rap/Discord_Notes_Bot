## DnD Discord Notes Bot

A Discord bot (currently a script) that records DnD sessions, transcribes them locally using Whisper, summarizes the transcript using a local LLM via Ollama, and automatically writes structured session notes to Notion/Discord.
Everything runs on your own machine — no audio, transcripts, or session data is ever sent to an external server.

### Tools:

- **Whisper** is speech recognition system by OpenAI (open-sourced): fully local, runs on CPU/GPU, free, no OpenAI account needed, no data leaving computer (https://github.com/openai/whisper)

- **py-cord** to build the Discord bot (free, account needed)

- **Ollama** for local LLMs (free), used for summarization

- **Notion client** (optional) - by default, the bot creates a Discord thread to post the meeting summary, but integration with Notion is also enabled

- Python version: 3.12

### Project Summary:
#### Phase 1 — Live Recording (during session)
- TBD

#### Phase 2 — Processing (after session)

- Whisper transcribes the merged WAV file entirely on-device
- Long transcripts are chunked
- Each chunk is summarized by the local LLM via Ollama
- Notes are written to a new Discord Thread (or Notion page via the Notion API)

### Bot Commands

- **!record** 
- **!stop** 
- **!notes** 

### Planned Improvements

- RAG — index past session notes so the LLM can cross-reference returning NPCs, locations, and plot threads
- Speaker diarization (with pyannote.audio?) — label who said what in the transcript
- !recap command — ask the bot questions about past sessions
- Automatic NPC page updates — append new info to existing NPC pages instead of duplicating
- Live notes during the session
- Fine-tuning? Probably over-kill for D&D. Or maybe RAG