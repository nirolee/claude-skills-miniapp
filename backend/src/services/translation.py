"""
翻译服务 - 支持多种翻译后端
"""
import os
import asyncio
import hashlib
import random
import time
from typing import Optional, List
import httpx
from anthropic import Anthropic
import logging

logger = logging.getLogger(__name__)


class TranslationService:
    """翻译服务基类"""

    async def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh') -> str:
        """翻译文本"""
        raise NotImplementedError


class BaiduTranslator(TranslationService):
    """百度翻译 API

    申请地址: https://fanyi-api.baidu.com/
    免费额度: 5万字符/月
    """

    def __init__(self, app_id: str, secret_key: str):
        self.app_id = app_id
        self.secret_key = secret_key
        self.endpoint = "https://fanyi-api.baidu.com/api/trans/vip/translate"

    def _generate_sign(self, query: str, salt: str) -> str:
        """生成签名"""
        sign_str = f"{self.app_id}{query}{salt}{self.secret_key}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    async def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh') -> str:
        """翻译文本"""
        if not text or not text.strip():
            return text

        # 百度翻译语言代码
        lang_map = {'en': 'en', 'zh': 'zh', 'auto': 'auto'}
        from_lang = lang_map.get(source_lang, 'auto')
        to_lang = lang_map.get(target_lang, 'zh')

        salt = str(random.randint(32768, 65536))
        sign = self._generate_sign(text, salt)

        params = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.endpoint, params=params)
                result = response.json()

                if 'error_code' in result:
                    logger.error(f"百度翻译错误: {result.get('error_msg')}")
                    return text

                trans_result = result.get('trans_result', [])
                if trans_result:
                    return trans_result[0].get('dst', text)

                return text

        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return text


class AnthropicTranslator(TranslationService):
    """使用 Claude API 翻译

    适合长文本翻译，质量高但成本较高
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh') -> str:
        """翻译文本"""
        if not text or not text.strip():
            return text

        lang_names = {
            'en': 'English',
            'zh': 'Chinese (Simplified)',
            'zh-cn': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)'
        }

        from_name = lang_names.get(source_lang.lower(), 'English')
        to_name = lang_names.get(target_lang.lower(), 'Chinese (Simplified)')

        prompt = f"""请将以下{from_name}文本翻译成{to_name}。
要求：
1. 保持技术术语的准确性
2. 保持Markdown格式（如果有）
3. 自然流畅，符合中文表达习惯
4. 只输出翻译结果，不要添加任何解释

原文：
{text}

翻译："""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()

        except Exception as e:
            logger.error(f"Claude翻译失败: {e}")
            return text


class TranslationManager:
    """翻译管理器 - 自动选择可用的翻译服务"""

    def __init__(self):
        self.translator: Optional[TranslationService] = None
        self._init_translator()

    def _init_translator(self):
        """初始化翻译服务"""
        # 优先使用百度翻译（免费额度）
        baidu_app_id = os.getenv('BAIDU_TRANSLATE_APP_ID')
        baidu_secret = os.getenv('BAIDU_TRANSLATE_SECRET')

        if baidu_app_id and baidu_secret:
            logger.info("使用百度翻译服务")
            self.translator = BaiduTranslator(baidu_app_id, baidu_secret)
            return

        # 备选: 使用 Anthropic Claude
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and anthropic_key != 'your_anthropic_api_key':
            logger.info("使用 Anthropic Claude 翻译服务")
            self.translator = AnthropicTranslator(anthropic_key)
            return

        logger.warning("未配置翻译服务，翻译功能将不可用")

    async def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh') -> Optional[str]:
        """翻译文本"""
        if not self.translator:
            logger.warning("翻译服务未配置")
            return None

        return await self.translator.translate(text, source_lang, target_lang)

    async def translate_batch(self, texts: List[str], source_lang: str = 'en', target_lang: str = 'zh', delay: float = 0.5) -> List[Optional[str]]:
        """批量翻译（带延迟避免限流）"""
        results = []
        for i, text in enumerate(texts):
            result = await self.translate(text, source_lang, target_lang)
            results.append(result)

            # 避免请求过快
            if i < len(texts) - 1:
                await asyncio.sleep(delay)

        return results


# 全局翻译管理器实例
translation_manager = TranslationManager()


# 便捷函数
async def translate_text(text: str, source_lang: str = 'en', target_lang: str = 'zh') -> Optional[str]:
    """翻译单个文本"""
    return await translation_manager.translate(text, source_lang, target_lang)


async def translate_skill_fields(name: str, description: str, content: str) -> dict:
    """翻译技能的所有字段"""
    results = await translation_manager.translate_batch([name, description, content], delay=1.0)

    return {
        'name_zh': results[0],
        'description_zh': results[1],
        'content_zh': results[2]
    }


if __name__ == "__main__":
    # 测试
    import asyncio

    async def test():
        # 测试短文本
        text = "Debug Code Skill"
        result = await translate_text(text)
        print(f"原文: {text}")
        print(f"译文: {result}")

    asyncio.run(test())
