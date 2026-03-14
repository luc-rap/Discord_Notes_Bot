## DnD Discord Notes Bot

A Discord bot that records DnD sessions, transcribes them locally using OpenAI Whisper, summarizes the transcript using a local LLM via Ollama, and automatically writes structured session notes to Notion/Discord.
Everything runs on your own machine — no audio, transcripts, or session data is ever sent to an external server.

### Tools:

- **Whisper** is speech recognition system by OpenAI (open-sourced): fully local, runs on CPU/GPU, free, no OpenAI account needed, no data leaving computer (https://github.com/openai/whisper)

- **py-cord** to build the Discord bot (free, account needed)

- **Ollama** for local LLMs (free), used for summarization

- **Notion client** (optional) - by default, the bot creates a Discord thread to post the meeting summary, but integration with Notion is also enabled

- Python version: 3.12

### Project Summary:
#### Phase 1 — Live Recording (during session)
- User types !record in Discord
- Bot joins the voice channel and begins capturing audio
- Each player's audio is recorded as a separate track/TBD/
- User types !stop to end the recording
- Individual tracks are merged into a single WAV file locally

#### Phase 2 — Processing (after session)

- User types !notes to trigger the pipeline
- Whisper transcribes the merged WAV file entirely on-device
- Long transcripts are chunked into ~3,000 word segments
- Each chunk is summarized by the local LLM via Ollama
- Chunk summaries are combined into final structured notes
- Notes are written to a new Discord Thread (or Notion page via the Notion API)

### Bot Commands

- **!record** Bot joins your voice channel and starts recording
- **!stop** Stops recording and saves the merged audio file
- **!notes** Runs full pipeline and posts notes to Notion

### Notes Structure

Each session generates with the following sections:

- Session Summary — 2-3 paragraph narrative recap written like a story
- Key Events — Chronological bullet list of major plot moments
- NPCs Encountered — Names, descriptions, and what was learned
- Player Decisions — Important choices made and potential consequences
- Loot & Rewards — Items, gold, XP, and level ups
- Loose Threads — Unresolved plot hooks to follow up on
- DM Notes — World-building details and things to remember

### Planned Improvements

- RAG — index past session notes so the LLM can cross-reference returning NPCs, locations, and plot threads
- Speaker diarization (with pyannote.audio?) — label who said what in the transcript
- !recap command — ask the bot questions about past sessions
- Automatic NPC page updates — append new info to existing NPC pages instead of duplicating
- Live notes during the session