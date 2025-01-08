import os

# OpenAI API配置
OPENAI_CONFIG = {
    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),  # 从环境变量获取，默认值为 OpenAI
    "api_key": os.getenv("OPENAI_API_KEY")
}

# 音频处理配置
# 大小为25MB、比特率为55kbps的mp3文件大约可以保存1小时的音频
# 大小为25MB、比特率为96kbps的mp3文件大约可以保存30分钟的音频
AUDIO_CONFIG = {
    "split_interval": 30 * 60 * 1000,   # 30分钟，单位为毫秒
    "max_file_size": 25 * 1024 * 1024,  # 25MB，单位为字节
    "language": "en",                   # 音频语言，中文为"zh"
    "export_format": "mp3",             # 分段后的音频导出格式
    "mp3_bitrate": "96k",               # 大于128kbps的MP3转换的目标比特率
}

# 输出配置
OUTPUT_CONFIG = {
    "segments_dir": "audio_segments",   # 音频分段存储目录
    "srt_dir": "srt_segments",          # SRT分段存储目录
    "transcripts_dir": "transcripts",   # 转录文本存放目录
    "converted_audio": "converted.mp3"  # 转换后的MP3文件，转录完成后自动清除
} 