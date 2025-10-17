"""
Конфигурация приложения AI Research Assistant
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Mistral AI API
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "your-mistral-api-key-here")
    MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
    MISTRAL_MODEL = "mistral-large-latest"
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # App Configuration
    APP_NAME = "AI Research Assistant"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Современное приложение для продуктового исследования с ИИ"
    
    # File Upload Configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx'}
    
    # Report Configuration
    MAX_REPORT_LENGTH = 50000  # Максимальная длина отчета
    REPORT_TIMEOUT = 300  # Таймаут генерации отчета (5 минут)
    
    @classmethod
    def validate_config(cls):
        """Проверяет корректность конфигурации"""
        errors = []
        
        if not cls.MISTRAL_API_KEY or cls.MISTRAL_API_KEY == "your-mistral-api-key-here":
            errors.append("MISTRAL_API_KEY не настроен. Добавьте ключ в .env файл")
        
        if cls.PORT < 1 or cls.PORT > 65535:
            errors.append("Некорректный порт. Должен быть от 1 до 65535")
        
        return errors

# Создаем экземпляр конфигурации
config = Config()
