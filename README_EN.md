# Whisper Audio Transcription Tool

A tool for transcribing audio files to subtitles or text using the Whisper API.

## Features

1. Supports multiple audio formats (mp3, m4a, wav, etc.)
2. Automatically handles audio files larger than 25MB using ffmpeg
   - First attempts to convert to lower bitrate MP3 (default 96kbps)
   - If still too large, performs lossless splitting
3. Supports batch processing
   - Can process single audio file
   - Can process all supported formats in a directory
4. Automatic timestamp handling (for subtitle formats)
   - Ensures correct timing in split transcriptions
   - Automatically merges split subtitle files
5. Intelligent text processing (for text format output)
   - Supports intelligent paragraph splitting
   - Automatic spelling and word usage check
   - Maintains original text integrity
6. Smart temporary file cleanup
   - Automatically cleans audio segment files
   - Automatically cleans intermediate transcription files
   - Automatically cleans converted MP3 files

## Configuration

### Environment Variables (.env file)
```
# OpenAI Whisper API Configuration
OPENAI_BASE_URL=your_whisper_api_url
OPENAI_API_KEY=your_whisper_api_key

# AI Configuration (Used for text format output processing)
AI_BASE_URL=your_ai_service_url
AI_API_KEY=your_ai_service_key
```

### AI Configuration (config.py)
```python
AI_CONFIG = {
    "provider": "your_provider",  # AI service provider
    "base_url": os.getenv("AI_BASE_URL"),
    "api_key": os.getenv("AI_API_KEY"),
    "model": "your_model_name",
    "system_prompt": """your system prompt"""
}
```

### Audio Processing Configuration (config.py)
```python
AUDIO_CONFIG = {
    "split_interval": 30 * 60 * 1000,  # 30 minutes
    "max_file_size": 25 * 1024 * 1024, # 25MB
    "language": "en",                  # Language setting
    "export_format": "mp3",            # Segment format
    "mp3_bitrate": "96k",              # Bitrate
    "response_format": "text"          # Output format
}
```

### Output Configuration (config.py)
```python
OUTPUT_CONFIG = {
    "audio_chunks_dir": "audio_chunks",  # Audio segments directory
    "trans_chunks_dir": "trans_chunks",  # Transcription segments directory
    "transcripts_dir": "transcripts",    # Final transcripts directory
    "converted_audio": "converted.mp3"   # Converted MP3 file
}
```

## Usage

1. Install Dependencies
```bash
pip install -r requirements.txt
```

2. Configure Environment Variables
   - Create .env file
   - Set necessary API keys and URLs

3. Run Script
```python
from whisper_sample import transcribe_audio

# Process single file or directory
audio_path = "path/to/your/audio"
transcribe_audio(audio_path)
```
Find transcribed files in the `transcripts` directory.

## Output Formats

Supports multiple output formats:
- text: Plain text format with intelligent paragraph splitting
- srt: Subtitle format with timestamps
- vtt: Web subtitle format
- json: JSON format with details
- verbose_json: JSON format with more details

## Notes

1. File Size Limits
   - Original files over 25MB are automatically converted
   - 96kbps MP3 can store about 30 minutes of audio
   - 55kbps MP3 can store about 1 hour of audio

2. Text Processing Features
   - Only processes text format output
   - Maintains original text without translation
   - Automatic spelling and word usage check

3. Dependencies
   - Python 3.6+
   - ffmpeg (system-level dependency, needs separate installation)
   - openai
   - python-dotenv
   - pydub