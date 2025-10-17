#!/bin/bash

# AI Research Assistant - Скрипт запуска
echo "🚀 Запуск AI Research Assistant..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверяем наличие pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден. Установите pip"
    exit 1
fi

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📚 Установка зависимостей..."
pip install -r requirements.txt

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создаем пример..."
    cat > .env << EOF
# Mistral AI API Configuration
MISTRAL_API_KEY=your-mistral-api-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
EOF
    echo "📝 Отредактируйте файл .env и добавьте ваш Mistral API ключ"
fi

# Запускаем приложение
echo "🎯 Запуск приложения..."
echo "📍 Адрес: http://localhost:8000"
echo "🔑 Убедитесь, что MISTRAL_API_KEY настроен в .env файле"
echo ""
echo "Для остановки нажмите Ctrl+C"

python run.py
