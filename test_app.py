#!/usr/bin/env python3
"""
Тестирование AI Research Assistant
"""

import requests
import json
import time

def test_app():
    """Тестирует основные функции приложения"""
    base_url = "http://localhost:8000"
    
    print("🧪 Тестирование AI Research Assistant...")
    
    # Тест 1: Главная страница
    print("\n1. Тестирование главной страницы...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Главная страница загружается")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Тест 2: Страница формы
    print("\n2. Тестирование страницы формы...")
    try:
        response = requests.get(f"{base_url}/feature")
        if response.status_code == 200:
            print("✅ Страница формы загружается")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: Отправка формы (без реального API ключа)
    print("\n3. Тестирование отправки формы...")
    form_data = {
        "product_description": "Тестовый продукт для банковских услуг",
        "segment": "ФЛ",
        "research_element": "авторизация",
        "benchmarks": "Сбербанк, Тинькофф",
        "required_players": "Visa, Mastercard",
        "required_countries": "Россия, США"
    }
    
    try:
        response = requests.post(f"{base_url}/process-feature", data=form_data)
        if response.status_code == 200:
            print("✅ Форма обрабатывается")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 4: Генерация отчета (только если API ключ настроен)
    print("\n4. Тестирование генерации отчета...")
    test_data = {
        "product_description": "Тестовый продукт",
        "segment": "ФЛ",
        "research_element": "тест",
        "benchmarks": "",
        "required_players": "",
        "required_countries": ""
    }
    
    try:
        response = requests.post(
            f"{base_url}/generate-report",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Отчет генерируется успешно")
            else:
                print(f"⚠️  Ошибка API: {result.get('message', 'Неизвестная ошибка')}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_app()
