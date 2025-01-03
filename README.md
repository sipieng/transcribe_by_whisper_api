# 音频转录工具

这是一个基于OpenAI Whisper API的音频转录工具，可以将音频文件转换为SRT格式的字幕文件。

## 主要功能

- 支持多种音频格式（mp3, m4a, wav等）
- 自动处理大于25MB的音频文件:
  - 检测音频比特率
  - 对高比特率文件(>128kbps)自动转换为低码率MP3
  - 对大文件自动进行无损分割
- 使用OpenAI的Whisper API进行语音转录
- 自动处理时间戳，确保分段转录后的字幕时间正确
- 支持清理临时文件，但保留最终转录结果

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
    "split_interval": 30 * 60 * 1000,    # 30分钟，单位为毫秒
    "max_file_size": 25 * 1024 * 1024,   # 25MB，单位为字节
    "language": "en",                     # 语言设置：中文为"zh"，英文为"en"
    "export_format": "mp3",               # 分段后的音频导出格式
    "mp3_bitrate": "96k"                 # MP3转换的目标比特率
}

OUTPUT_CONFIG = {
    "segments_dir": "segments",           # 音频分段目录
    "srt_dir": "srt_segments",           # 字幕分段目录
    "final_output": "transcription.srt",  # 最终输出的字幕文件
    "converted_audio": "converted.mp3"    # 转换后的音频文件
}
```

## 使用方法

```python
from whisper_sample import transcribe_audio

# 指定音频文件路径
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
4. 对分段转录结果进行时间戳调整
5. 合并所有分段为最终SRT文件
6. 询问是否清理临时文件

## 输出文件

- `transcription.srt`: 最终的字幕文件
- `segments/`: 音频分段临时目录
- `srt_segments/`: 字幕分段临时目录
- `converted.mp3`: 转换后的临时音频文件

## 注意事项

- 确保系统已正确安装FFmpeg
- 请确保OpenAI API密钥配置正确
- 临时文件可以在转录完成后选择清理
