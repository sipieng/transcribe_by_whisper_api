import os

# AI配置（用于处理text格式）
AI_CONFIG = {
    "provider": "anthropic",  # AI服务提供商
    "base_url": os.getenv("AI_BASE_URL", "https://api.anthropic.com"),
    "api_key": os.getenv("AI_API_KEY"),
    "model": "claude-3-5-sonnet-20241022",  # 使用的模型名称
    "system_prompt": """
在这个对话中，我会提供一些英文。请你：
1. 通读并理解我提供的英文文本；
2. 根据内容逻辑进行合理分段；
3. 不要给每个分段添加标题或者解释，直接输出分段内容；
4. 保持原文不变，不要进行翻译，不要进行任何增加、删除或者修改，包括你认为可能是文章来源的那部分；
5. 如果发现可能有拼写错误或者使用错误的用词，请在底部指出并说明修改建议及依据。
英文内容如下：
"""
}

# OpenAI Whisper API配置
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
    "response_format": "srt"            # Whisper API的响应格式，可选值：srt, text, json, verbose_json, vtt
}

# 输出配置
OUTPUT_CONFIG = {
    "audio_chunks_dir": "audio_chunks",  # 音频分段存储目录
    "trans_chunks_dir": "trans_chunks",  # 转录分段临时存储目录
    "transcripts_dir": "transcripts",    # 转录文本存放目录
    "converted_audio": "converted.mp3"   # 转换后的MP3文件，转录完成后自动清除
} 