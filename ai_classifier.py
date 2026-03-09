"""
AI Classification module for message analysis
Uses OpenRouter API to classify messages as 'seeker' or 'marketer'
"""

import aiohttp
import json
import asyncio
import logging
from typing import Dict, Optional, Any
from db import get_setting

logger = logging.getLogger(__name__)

# Detailed prompt for AI classification
CLASSIFICATION_PROMPT = """
أنت مساعد ذكي متخصص في تحليل رسائل تليجرام وتصنيف المرسلين بدقة عالية. المهمة: تحديد ما إذا كان المرسل **طالباً يطلب مساعدة** (seeker) أم **معلناً يروج لخدمات** (marketer).

### **معايير التصنيف الدقيقة**

#### **أولاً: فئة الطالب (seeker)**
- السمات: يطلب مساعدة في مجاله الدراسي أو الأكاديمي.
- أمثلة حقيقية:
  - "حد يعرف دكتور يشرح عملي الفارما؟"
  - "أبي أحد يحل واجب الرياضيات ضروري"
  - "من يعرف مدرس خصوصي للفيزياء؟"
  - "تعرفون أحد يسوي لي بروجكت تخرج؟"
  - "محتاج بحث عن الذكاء الاصطناعي"

#### **ثانياً: فئة المعلن (marketer)**
- السمات:
  - يقدم خدمات تجارية (مدفوعة).
  - يحتوي على روابط واتساب أو تليجرام للتواصل.
  - قوائم طويلة بالخدمات (مثل: نقدم لكم، لدينا، خدمات طلابية، ...).
  - استخدام رموز تزيينية لجذب الانتباه: ⭐, ✅, ═════, ☆, 💯, 🎓, 📚, 💻, 📞.
  - تكرار نفس الرسالة في عدة مجموعات.
  - عبارات مثل: "للتواصل خاص"، "للاستفسار واتساب"، "عروض حصرية"، "ضمان الجودة".

### **تعليمات خاصة للمقارنة**
- إذا كانت الرسالة تحتوي على روابط (واتساب، تليجرام) + قائمة خدمات → **marketer**.
- إذا كانت الرسالة استفهاماً (علامة استفهام) وتخلو من الروابط وقوائم الخدمات → **seeker**.
- إذا كانت الرسالة طويلة ومنسقة (نقاط، رموز) وتدعو للتواصل → **marketer**.
- انتبه للهجة الخليجية: عبارات مثل "أبي أحد"، "تعرفون حد"، "من يعرف" تدل على طالب، بينما "نقدم لكم"، "لدينا"، "للتواصل" تدل على معلن.

### **المخرجات المطلوبة**
يجب أن تكون النتيجة بصيغة JSON فقط ولا تحتوي على أي نص آخر. على سبيل المثال:
- لطالب: {"type": "seeker", "confidence": 95, "reason": "يطلب مساعدة في شرح مادة، ولا توجد أي روابط أو عروض تجارية."}
- لمعلن: {"type": "marketer", "confidence": 98, "reason": "يقدم قائمة خدمات طلابية مع رابط واتساب، ويستخدم رموز ترويجية."}

الرسالة المراد تحليلها:
{message}
"""

class AIClassifier:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_setting('openrouter_api_key')
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.timeout = 30
        self.model = "qwen/qwen-2.5-72b-instruct"  # Fallback model
        
    async def classify_message(self, message_text: str) -> Dict[str, Any]:
        """
        Classify a message as seeker or marketer
        Returns: {type: 'seeker'|'marketer', confidence: 0-100, reason: str}
        """
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured, returning default classification")
            return {
                "type": "seeker",
                "confidence": 0,
                "reason": "API key not configured - defaulting to seeker"
            }
        
        try:
            prompt = CLASSIFICATION_PROMPT.format(message=message_text)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://telegram-radar.local",
                "X-Title": "Telegram Radar"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        logger.error(f"OpenRouter API error: {response.status}")
                        return {
                            "type": "seeker",
                            "confidence": 0,
                            "reason": f"API error: {response.status}"
                        }
                    
                    data = await response.json()
                    
                    if 'choices' not in data or len(data['choices']) == 0:
                        logger.error("Invalid API response format")
                        return {
                            "type": "seeker",
                            "confidence": 0,
                            "reason": "Invalid API response"
                        }
                    
                    content = data['choices'][0]['message']['content']
                    
                    # Parse JSON response
                    try:
                        result = json.loads(content)
                        # Validate result structure
                        if 'type' in result and 'confidence' in result:
                            return {
                                "type": result.get('type', 'seeker'),
                                "confidence": min(100, max(0, result.get('confidence', 0))),
                                "reason": result.get('reason', '')
                            }
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON response: {content}")
                        return {
                            "type": "seeker",
                            "confidence": 0,
                            "reason": "Failed to parse AI response"
                        }
                    
                    return {
                        "type": "seeker",
                        "confidence": 0,
                        "reason": "Unexpected response format"
                    }
                    
        except asyncio.TimeoutError:
            logger.error("OpenRouter API timeout")
            return {
                "type": "seeker",
                "confidence": 0,
                "reason": "API timeout"
            }
        except Exception as e:
            logger.error(f"Error classifying message: {str(e)}")
            return {
                "type": "seeker",
                "confidence": 0,
                "reason": f"Error: {str(e)}"
            }

async def classify_message_async(message_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Async wrapper for message classification"""
    classifier = AIClassifier(api_key)
    return await classifier.classify_message(message_text)
