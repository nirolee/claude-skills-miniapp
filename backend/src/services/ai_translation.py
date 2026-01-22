"""
AI翻译服务 - 使用Claude进行高质量翻译
"""
from typing import Optional, Dict, Any
from anthropic import AsyncAnthropic
import logging
import json

logger = logging.getLogger(__name__)


class AITranslator:
    """AI翻译器 - 使用Claude API"""

    def __init__(self, client: AsyncAnthropic):
        """
        初始化翻译器

        Args:
            client: Anthropic AI 客户端（通过依赖注入提供）
        """
        self.client = client
        # 使用 Sonnet 4.5 确保兼容性
        self.model = "claude-sonnet-4-5-20250929"

    async def translate_text(
        self, text: str, source_lang: str = "en", target_lang: str = "zh"
    ) -> Optional[str]:
        """
        翻译单个文本

        Args:
            text: 待翻译文本
            source_lang: 源语言
            target_lang: 目标语言

        Returns:
            翻译后的文本，失败返回None
        """
        if not text or not text.strip():
            return text

        lang_names = {
            "en": "English",
            "zh": "Chinese (Simplified)",
            "zh-cn": "Chinese (Simplified)",
            "zh-tw": "Chinese (Traditional)",
        }

        from_name = lang_names.get(source_lang.lower(), "English")
        to_name = lang_names.get(target_lang.lower(), "Chinese (Simplified)")

        prompt = f"""请将以下{from_name}文本翻译成{to_name}。

要求：
1. 保持技术术语的准确性（如 Claude Code、Debug、Skill 等保持原文或采用通用译法）
2. 保持 Markdown 格式（如果有）
3. 自然流畅，符合中文表达习惯
4. 只输出翻译结果，不要添加任何解释

原文：
{text}

翻译："""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            # 提取翻译结果
            translated = response.content[0].text.strip()

            logger.info(f"翻译成功: {text[:50]}...")
            return translated

        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return None

    async def translate_skill_fields(
        self, name: str, description: str, content: str
    ) -> Dict[str, Optional[str]]:
        """
        翻译技能的所有字段（批量优化版本）

        Args:
            name: 技能名称
            description: 技能描述
            content: 技能内容（完整Markdown）

        Returns:
            包含翻译结果的字典
        """
        # 如果 content 很长，分开翻译以获得更好的质量
        if len(content) > 3000:
            logger.info(f"Content 较长 ({len(content)} 字符)，将单独翻译")

            # 分别翻译
            name_zh = await self.translate_text(name)
            description_zh = await self.translate_text(description)
            content_zh = await self.translate_text(content)

            return {
                "name_zh": name_zh,
                "description_zh": description_zh,
                "content_zh": content_zh,
            }

        # 短内容：使用单次请求翻译所有字段（更经济）
        # 使用 JSON 转义避免格式问题
        import json as json_lib

        prompt = f"""请将以下 Claude Code Skill 的信息翻译成中文。

要求：
1. 保持技术术语准确性（如 Claude Code、Debug、API 等专业术语）
2. 完整保持 Markdown 格式（标题、列表、代码块、链接等）
3. 自然流畅的中文表达
4. 以JSON格式返回结果

原文：
{json_lib.dumps({
    "name": name,
    "description": description,
    "content": content
}, ensure_ascii=False, indent=2)}

请翻译后返回JSON格式：
{{
    "name_zh": "翻译后的名称",
    "description_zh": "翻译后的描述",
    "content_zh": "翻译后的完整内容（保持Markdown格式）"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=16384,  # 增加 token 限制以支持更长内容
                messages=[{"role": "user", "content": prompt}],
            )

            result_text = response.content[0].text

            # 提取JSON（处理可能的markdown代码块）
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()

            result = json.loads(result_text)

            logger.info(f"技能翻译成功: {name}")
            return {
                "name_zh": result.get("name_zh"),
                "description_zh": result.get("description_zh"),
                "content_zh": result.get("content_zh"),
            }

        except Exception as e:
            logger.error(f"批量翻译失败: {str(e)}")
            # 降级：逐个翻译
            logger.info("降级为逐个翻译")
            return {
                "name_zh": await self.translate_text(name),
                "description_zh": await self.translate_text(description),
                "content_zh": await self.translate_text(content),
            }


# 创建全局翻译器实例
_translator_instance: Optional[AITranslator] = None


def get_translator() -> AITranslator:
    """获取翻译器实例（单例模式）"""
    global _translator_instance

    if _translator_instance is None:
        # 从配置系统获取 API 配置
        from src.config import get_settings
        from anthropic import AsyncAnthropic

        settings = get_settings()
        config = settings.get_anthropic_config()

        # 如果配置中有 api_key，使用配置创建客户端
        if config:
            client = AsyncAnthropic(**config)
        else:
            # 否则让 SDK 自动从环境变量读取
            client = AsyncAnthropic()

        _translator_instance = AITranslator(client)

        # 记录配置来源
        if config.get('api_key'):
            logger.info("✅ Anthropic API 配置已加载（来源：配置文件或 Claude Code）")
        else:
            logger.info("✅ Anthropic API 配置已加载（来源：系统环境变量）")

    return _translator_instance


# 便捷函数
async def translate_text(
    text: str, source_lang: str = "en", target_lang: str = "zh"
) -> Optional[str]:
    """翻译单个文本"""
    translator = get_translator()
    return await translator.translate_text(text, source_lang, target_lang)


async def translate_skill_fields(
    name: str, description: str, content: str
) -> Dict[str, Optional[str]]:
    """翻译技能的所有字段"""
    translator = get_translator()
    return await translator.translate_skill_fields(name, description, content)


if __name__ == "__main__":
    # 测试
    import asyncio

    async def test():
        text = "Debug Code Skill - Automatically detect and fix code errors"
        result = await translate_text(text)
        print(f"原文: {text}")
        print(f"译文: {result}")

    asyncio.run(test())
