#!/usr/bin/env python3
"""
Запуск AI Research Assistant
"""

import uvicorn
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

if __name__ == "__main__":
    # Получаем настройки из переменных окружения
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print("🚀 Запуск AI Research Assistant...")
    print(f"📍 Адрес: http://{host}:{port}")
    print("🔑 Убедитесь, что MISTRAL_API_KEY настроен в .env файле")
    
    # Запускаем сервер
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
