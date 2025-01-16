# Whisper Audio Transcription Tool

这是一个使用 Whisper API 将音频文件转录为字幕或文本文件的工具。

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
5. 智能文本处理（针对输出为text格式）
   - 支持对转录文本进行智能分段
   - 自动检查拼写和用词问题
   - 保持原文完整性
6. 智能清理临时文件
   - 自动清理音频分段文件
   - 自动清理中间过程生成的转录文件
   - 自动清理转换后的MP3文件

## 配置说明

### 环境变量配置（.env文件）
```
# OpenAI Whisper API配置
OPENAI_BASE_URL=your_whisper_api_url
OPENAI_API_KEY=your_whisper_api_key

# AI配置（当输出格式为`text`时，使用AI对整段文本进行智能分段）
AI_BASE_URL=your_ai_service_url
AI_API_KEY=your_ai_service_key
```

### AI配置（config.py）
```python
AI_CONFIG = {
    "provider": "your_provider",  # AI服务提供商
    "base_url": os.getenv("AI_BASE_URL"),
    "api_key": os.getenv("AI_API_KEY"),
    "model": "your_model_name",
    "system_prompt": """你的系统提示词"""
}
```

### 音频处理配置（config.py）
```python
AUDIO_CONFIG = {
    "split_interval": 30 * 60 * 1000,  # 30分钟
    "max_file_size": 25 * 1024 * 1024, # 25MB
    "language": "en",                  # 语言设置
    "export_format": "mp3",            # 分段格式
    "mp3_bitrate": "96k",              # 比特率
    "response_format": "text"          # 输出格式
}
```

### 输出配置（config.py）
```python
OUTPUT_CONFIG = {
    "audio_chunks_dir": "audio_chunks",  # 音频分段存储目录
    "trans_chunks_dir": "trans_chunks",  # 转录分段临时存储目录
    "transcripts_dir": "transcripts",    # 转录文本存放目录
    "converted_audio": "converted.mp3"   # 转换后的MP3文件
}
```

## 使用说明

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
   - 创建 .env 文件
   - 设置必要的API密钥和URL

3. 运行脚本
```python
from whisper_sample import transcribe_audio

# 处理单个文件或目录
audio_path = "path/to/your/audio"
transcribe_audio(audio_path)
```
之后可在`transcripts`目录下找到转录后的文件。

## 输出格式

支持多种输出格式：
- text: 纯文本格式，会进行智能分段
- srt: 字幕格式，包含时间戳
- vtt: 网页字幕格式
- json: JSON格式的详细信息
- verbose_json: 包含更多细节的JSON格式

## 注意事项

1. 文件大小限制
   - 原始文件超过25MB会自动转换
   - 96kbps的MP3约可存储30分钟音频
   - 55kbps的MP3约可存储1小时音频

2. 文本处理功能
   - 仅对 text 格式的输出进行处理
   - 保持原文不变，不进行翻译
   - 自动检查拼写和用词问题

3. 依赖要求
   - Python 3.6+
   - ffmpeg（系统级依赖，需要单独安装）
   - openai
   - python-dotenv
   - pydub
