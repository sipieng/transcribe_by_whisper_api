import os

# OpenAI API配置
OPENAI_CONFIG = {
    "base_url": "https://yunwu.ai/v1",  # 直接使用固定值
    "api_key": os.getenv("OPENAI_API_KEY")  # 只有 API key 从环境变量获取
}

# 音频处理配置
# 大小为25MB、比特率为55kbps的mp3文件大约可以保存1小时的音频
# 大小为25MB、比特率为96kbps的mp3文件大约可以保存30分钟的音频
AUDIO_CONFIG = {
    "split_interval": 30 * 60 * 1000,  # 30分钟，单位为毫秒
    "max_file_size": 25 * 1024 * 1024,  # 25MB，单位为字节
    "language": "en",  # 语言设置：中文为"zh"，英文为"en"
    "export_format": "mp3",  # 分段后的音频导出格式
    "mp3_bitrate": "96k", #"55k"  # MP3转换的目标比特率
}

# 输出配置
OUTPUT_CONFIG = {
    "segments_dir": "segments",  # 音频分段存储目录
    "srt_dir": "srt_segments",   # SRT分段存储目录
    "final_output": "transcription.srt",  # 最终合并的SRT文件
    "converted_audio": "converted.mp3"  # 转换后的MP3文件
} 