# Whisper Audio Transcription Tool

这是一个使用 OpenAI Whisper API 将音频文件转录为字幕或文本文件的工具。

## 功能特点

1. 支持多种音频格式（mp3, m4a, wav等）
2. 使用 ffmpeg 自动处理大于25MB的音频文件
   - 先尝试转换为低码率MP3（默认96kbps）
   - 如果仍然过大，则进行无损分割
3. 支持批量处理
   - 可以处理单个音频文件
   - 可以处理整个目录下的所有支持格式的音频文件
4. 自动处理时间戳（适用于字幕格式）
   - 确保分段转录后的字幕时间正确
   - 自动合并多个分段的字幕文件
5. 智能清理临时文件
   - 自动清理音频分段文件
   - 自动清理中间过程生成的转录文件
   - 自动清理转换后的MP3文件

## 配置说明

### 环境变量配置（.env文件）

```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，默认为 OpenAI 官方 API
```

## 环境要求

- Python 3.x
- FFmpeg（用于音频处理）
- 以下Python包:
  ```bash
  pip install openai python-dotenv pydub
  ```

## 配置说明

1. 创建`.env`文件并配置必要的环境变量:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，默认为 OpenAI 官方 API
```

2. 在`config.py`中配置相关参数:
```python
OPENAI_CONFIG = {
    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),  # 从环境变量获取
    "api_key": os.getenv("OPENAI_API_KEY")
}

AUDIO_CONFIG = {
    "split_interval": 30 * 60 * 1000,     # 30分钟，单位为毫秒
    "max_file_size": 25 * 1024 * 1024,    # 25MB，单位为字节
    "language": "en",                     # 语言设置：中文为"zh"，英文为"en"
    "export_format": "mp3",               # 分段后的音频导出格式
    "mp3_bitrate": "96k",                 # MP3转换的目标比特率
    "response_format": "text"             # 转录格式：srt, text, json, verbose_json, vtt
}

OUTPUT_CONFIG = {
    "audio_chunks_dir": "audio_chunks",   # 音频分段存储目录
    "trans_chunks_dir": "trans_chunks",   # 转录分段临时存储目录
    "transcripts_dir": "transcripts",     # 转录文本存放目录
    "converted_audio": "converted.mp3"    # 转换后的MP3文件，转录完成后自动清除
} 
```

## 使用方法

```python
from whisper_sample import transcribe_audio

# 指定音频文件路径，可以是单个文件或文件夹
audio_file_path = "path/to/your/audio.mp3"

# 开始转录
transcribe_audio(audio_file_path)
```

## 工作流程

1. 检查音频文件大小
2. 如果文件>25MB:
   - 检查音频比特率
   - 如果>128kbps，转换为低码率MP3
   - 如果文件仍>25MB，进行分段处理
3. 使用Whisper API进行转录
4. 对分段转录结果进行时间戳调整（仅适用于字幕格式）
5. 合并所有分段为最终文件
6. 清理临时文件

## 输出文件

- `transcripts/*`: 转录完成的文件储存在 transcripts 目录下
  - 文件扩展名根据 response_format 自动设置（.srt/.txt/.json/.vtt）
- `audio_chunks/`: 音频分段临时目录
- `trans_chunks/`: 转录分段临时目录
- `converted.mp3`: 转换后的临时音频文件，转换完成后删除

## 注意事项

- 确保系统已正确安装FFmpeg
- 请确保OpenAI API密钥配置正确
- 字幕时间戳调整功能仅在使用 srt 或 vtt 格式时有效
