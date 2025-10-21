from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import asyncio
import os
import uuid
from dotenv import load_dotenv
import json
from datetime import datetime
from config import config
from database import init_database, get_db, ResearchReport, UserSession
from services import ReportService, SessionManager
from sqlalchemy.orm import Session

load_dotenv()

app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    print("✅ Database initialized")

# Проверяем конфигурацию при запуске
config_errors = config.validate_config()
if config_errors:
    print("⚠️  Предупреждения конфигурации:")
    for error in config_errors:
        print(f"   - {error}")

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/feature", response_class=HTMLResponse)
async def feature_form(request: Request):
    return templates.TemplateResponse("feature_form.html", {"request": request})

@app.get("/product", response_class=HTMLResponse)
async def product_form(request: Request):
    return templates.TemplateResponse("product_form.html", {"request": request})

@app.post("/process-feature")
async def process_feature(
    request: Request,
    product_description: str = Form(...),
    segment: str = Form(...),
    research_element: str = Form(...),
    benchmarks: str = Form(""),
    required_players: str = Form(""),
    required_countries: str = Form(""),
    db: Session = Depends(get_db)
):
    # Сохраняем данные для обработки
    research_data = {
        "product_description": product_description,
        "segment": segment,
        "research_element": research_element,
        "benchmarks": benchmarks,
        "required_players": required_players,
        "required_countries": required_countries
    }
    
    return templates.TemplateResponse("loading.html", {
        "request": request,
        "research_data": research_data
    })

@app.post("/process-product")
async def process_product(
    request: Request,
    product_description: str = Form(...),
    segment: str = Form(...),
    product_characteristics: str = Form(...),
    required_players: str = Form(""),
    required_countries: str = Form(""),
    db: Session = Depends(get_db)
):
    # Сохраняем данные для обработки
    research_data = {
        "product_description": product_description,
        "segment": segment,
        "product_characteristics": product_characteristics,
        "required_players": required_players,
        "required_countries": required_countries
    }
    
    return templates.TemplateResponse("loading.html", {
        "request": request,
        "research_data": research_data
    })

@app.post("/generate-report")
async def generate_report(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    # Извлекаем данные из запроса
    product_description = data.get('product_description', '')
    segment = data.get('segment', '')
    research_element = data.get('research_element', '')
    benchmarks = data.get('benchmarks', '')
    required_players = data.get('required_players', '')
    required_countries = data.get('required_countries', '')
    
    # Новые поля для исследования продукта
    product_characteristics = data.get('product_characteristics', '')
    
    # Определяем тип исследования
    research_type = "feature" if research_element else "product"
    
    # Создаем промпт для Mistral в зависимости от типа исследования
    if research_type == "feature":
        prompt = f"""
Роль

Ты — старший аналитик по финтеху/банкам/супераппам. Работаешь как исследователь рынка + UX-разведчик: быстро находишь и верифицируешь продуктовые фичи у международных игроков и формируешь пригодные к внедрению инсайты для Product Manager.

Цель

Собрать и проверить лучшие практики/фичи по заданному элементу продукта.

Показать применимость к нашему контексту (value, риски, усилия внедрения).

Дать минимум 10 подтверждённых кейсов с источниками и скриншотами.

Входные параметры (подставь из запроса)
- Описание продукта и бизнес-контекста: {product_description}
- Сегмент: {segment}
- Что исследуем (элемент продукта): {research_element}
- Известные бенчмарки (если есть): {benchmarks}
- Обязательные игроки к рассмотрению (если есть): {required_players}
- Обязательные страны к рассмотрению (если есть): {required_countries}

Обязательные источники и приоритет
- Официальные сайты/документы компаний (прайсы, релизы, справки, help-центры).
- Отчёты консалтинга/исследовательских агентств (в т.ч. UX/UI).
- Карточки приложений в App Store / Google Play (описания, скриншоты, отзывы).
- Профильные медиа/новости, тех-блоги компаний.
- Другие релевантные источники.
На каждый факт давай ссылку. Если данные спорные — пометь «(требует верификации)».

Метод

Сначала коротко сформулируй гипотезы пользы фичи для нашего контекста.

Делай целенаправленные запросы по странам/игрокам/кейвордам.

Для каждой фичи: фиксируй первоисточник, дату публикации/обновления и географию доступности.

Проверяй актуальность (дата релиза/последнего апдейта, наличие в текущей версии приложения).

Формат итоговой выдачи
1) Executive Summary (до 10 пунктов)

Что нашли, почему важно, краткий список «quick wins», риски и зависимости.

2) 10+ кейсов (по шаблону, строго пронумеруй)

Компания: Название — ссылка на сайт.

Краткое описание (1 предложение): ...

Страна регистрации: ...

Подробное описание фичи (4–5 предложений):
— Как работает / где в пользовательском пути.
— Для кого / какие триггеры.
— Метрики/результаты (если есть, со ссылкой).

Ссылки на источники: полный список, каждая ссылка отдельным пунктом.

Скриншоты фичи: вставь изображения; подпиши, что на них (экран/шаг/состояние).

Перевод скриншотов (если не RU/EN): полный, с разбивкой по блокам.

4) Применимость к нашему продукту

Mapping к нашим целям/метрикам: какие north-star/подметрики заденет.

Локализация и регуляторика: AML/KYC, платежные лицензии, персональные данные, санкционные и иные ограничения.

Технические зависимости: данные/интеграции, изменения в бэке/клиенте, аналитика.

Риски и способы их снижения.
Требования к качеству
Минимум 10 кейсов, лучше 12–15, но без «воды».

Все факты — с активными ссылками на первоисточники.

Даты релизов/обновлений указывать в каждом кейсе.

Не использовать непроверяемые источники; если используешь обзоры/агрегаторы — обязательно находи первоисточник.

Отмечай гео-ограничения фич (доступность по странам/рынкам).

Если чего-то не нашлось, так и напиши «не найдено/редко встречается», предложи обходные пути поиска.

Что исключить

Голые мнения без подтверждений.

Копирование маркетинговых лозунгов без верификации в продукте.

Скриншоты без подписи и контекста.

«Списки без анализа применимости».

Проверки перед сдачей (чек-лист)

 10+ кейсов, пронумерованы.

 В каждом кейсе есть: сайт компании, страна, 4–5 предложений о фиче, источники, скриншоты, подписи, перевод при необходимости.

 Таблица обзора заполнена для всех кейсов.

 Указаны даты публикаций/обновлений.

 Есть секция «Применимость» и «План внедрения».

 Все ссылки открываются.

Тон и стиль

Нейтрально-деловой, кратко, по делу.

Сначала выводы, потом детали.

Ясные формулировки, избегай жаргона.
"""
    else:  # research_type == "product"
        prompt = f"""
Роль

Ты — старший аналитик по финтеху/банкам/супераппам. Работаешь как исследователь рынка + UX-разведчик: быстро находишь новые продукты международных игроков и формируешь пригодные к внедрению инсайты для Product Manager. 

Цель

Собрать и проверить наиболее подходящие продукты по описанию Product Manager. 

Показать применимость к нашему контексту (value, риски, усилия внедрения).

Дать минимум 10 подтверждённых кейсов с источниками и скриншотами.

Входные параметры (подставь из запроса)
- Описание бизнес-контекста: {product_description}
- Сегмент: {segment}
- Характеристики продукта, который требуется найти: {product_characteristics}
- Обязательные игроки к рассмотрению (если есть): {required_players}
- Обязательные страны к рассмотрению (если есть): {required_countries}

Обязательные источники и приоритет
- Официальные сайты/документы компаний (прайсы, релизы, справки, help-центры).
- Отчёты консалтинга/исследовательских агентств (в т.ч. UX/UI).
- Карточки приложений в App Store / Google Play (описания, скриншоты, отзывы).
- Профильные медиа/новости, тех-блоги компаний.
- Другие релевантные источники.
На каждый факт давай ссылку. Если данные спорные — пометь «(требует верификации)».

Метод

Сначала коротко сформулируй гипотезы пользы продукта для бизнеса. 

Делай целенаправленные запросы по странам/игрокам/кейвордам.

Для каждого продукта: фиксируй первоисточник, дату публикации/обновления и географию доступности. 

Проверяй актуальность (дата релиза/последнего апдейта, наличие в текущей версии приложения).

Формат итоговой выдачи
1) Executive Summary (до 10 пунктов)

Что нашли, почему важно, краткий список «quick wins», риски и зависимости.

2) 10+ кейсов (по шаблону, строго пронумеруй)

Компания: Название — ссылка на сайт.

Краткое описание (1 предложение): ...

Страна регистрации: ...

Подробное описание продукта (4–5 предложений): 
— Как работает / как устроен UX/UI 
— Для кого / какие триггеры.
— Метрики/результаты (если есть, со ссылкой).

Ссылки на источники: полный список, каждая ссылка отдельным пунктом.

Скриншоты продукта: вставь изображения; подпиши, что на них (экран/шаг/состояние). 

Перевод скриншотов (если не RU/EN): полный, с разбивкой по блокам.

4) Применимость к нашему бизнесу

Mapping к нашим целям/метрикам: какие north-star/подметрики заденет.

Локализация и регуляторика: AML/KYC, платежные лицензии, персональные данные, санкционные и иные ограничения.

Технические зависимости: данные/интеграции, изменения в бэке/клиенте, аналитика.

Риски и способы их снижения.
Требования к качеству
Минимум 10 кейсов, лучше 12–15, но без «воды».

Все факты — с активными ссылками на первоисточники.

Даты релизов/обновлений указывать в каждом кейсе.

Не использовать непроверяемые источники; если используешь обзоры/агрегаторы — обязательно находи первоисточник.

Отмечай гео-ограничения продуктов (доступность по странам/рынкам). 

Если чего-то не нашлось, так и напиши «не найдено/редко встречается», предложи обходные пути поиска.

Что исключить

Голые мнения без подтверждений.

Копирование маркетинговых лозунгов без верификации в продукте.

Скриншоты без подписи и контекста.

«Списки без анализа применимости».

Проверки перед сдачей (чек-лист)

 10+ кейсов, пронумерованы.

 В каждом кейсе есть: сайт компании, страна, 4–5 предложений о продукте, источники, скриншоты, подписи, перевод при необходимости. 

 Таблица обзора заполнена для всех кейсов.

 Указаны даты публикаций/обновлений.

 Есть секция «Применимость» и «План внедрения».

 Все ссылки открываются.

Тон и стиль

Нейтрально-деловой, кратко, по делу.

Сначала выводы, потом детали.

Ясные формулировки, избегай жаргона.
"""

    # Отправляем запрос к Mistral API
    async with httpx.AsyncClient(timeout=config.REPORT_TIMEOUT) as client:
        response = await client.post(
            config.MISTRAL_API_URL,
            headers={
                "Authorization": f"Bearer {config.MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.MISTRAL_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            report_content = result["choices"][0]["message"]["content"]
            
            # Сохраняем отчет в базу данных
            report_service = ReportService(db)
            session_manager = SessionManager(db)
            
            # Получаем или создаем сессию
            session_id = request.cookies.get("session_id")
            if not session_id:
                session_id = session_manager.create_session(
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent")
                )
            
            # Создаем отчет
            if research_type == "feature":
                title = f"Исследование: {research_element}"
                report = report_service.create_report(
                    title=title,
                    content=report_content,
                    research_type="feature",
                    product_description=product_description,
                    segment=segment,
                    research_element=research_element,
                    benchmarks=benchmarks,
                    required_players=required_players,
                    required_countries=required_countries,
                    session_id=session_id,
                    ai_model=config.MISTRAL_MODEL,
                    processing_time=30,  # Примерное время
                    tokens_used=len(report_content.split())  # Примерное количество токенов
                )
            else:  # research_type == "product"
                title = f"Исследование продукта: {product_characteristics[:50]}..."
                report = report_service.create_report(
                    title=title,
                    content=report_content,
                    research_type="product",
                    product_description=product_description,
                    segment=segment,
                    research_element=product_characteristics,  # Используем характеристики продукта
                    benchmarks="",  # Не используется для product
                    required_players=required_players,
                    required_countries=required_countries,
                    session_id=session_id,
                    ai_model=config.MISTRAL_MODEL,
                    processing_time=30,  # Примерное время
                    tokens_used=len(report_content.split())  # Примерное количество токенов
                )
            
            return {
                "success": True,
                "report": report_content,
                "report_id": report.id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"API Error: {response.status_code}",
                "message": "Ошибка при генерации отчета"
            }

@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request, report_id: int = None, db: Session = Depends(get_db)):
    report_content = ""
    report_title = "Отчет не найден"
    
    if report_id:
        # Загружаем отчет из базы данных
        report_service = ReportService(db)
        report = report_service.get_report(report_id)
        if report:
            report_content = report.content
            report_title = report.title
        else:
            report_content = "Отчет с указанным ID не найден."
    else:
        # Получаем report из query параметра (для обратной совместимости)
        report = request.query_params.get("report", "")
        report_content = report
        report_title = "Результат исследования"
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "report": report_content,
        "report_id": report_id,
        "report_title": report_title
    })

@app.get("/reports")
async def get_reports(request: Request, db: Session = Depends(get_db)):
    """Получить список отчетов"""
    report_service = ReportService(db)
    session_id = request.cookies.get("session_id")
    
    if session_id:
        reports = report_service.get_reports_by_session(session_id)
    else:
        reports = report_service.get_recent_reports(10)
    
    return {
        "reports": [
            {
                "id": report.id,
                "title": report.title,
                "research_type": report.research_type,
                "created_at": report.created_at.isoformat(),
                "research_element": report.research_element
            }
            for report in reports
        ]
    }

@app.get("/reports/{report_id}")
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """Получить конкретный отчет"""
    report_service = ReportService(db)
    report = report_service.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": report.id,
        "title": report.title,
        "content": report.content,
        "research_type": report.research_type,
        "created_at": report.created_at.isoformat(),
        "research_element": report.research_element,
        "segment": report.segment,
        "benchmarks": report.benchmarks,
        "required_players": report.required_players,
        "required_countries": report.required_countries
    }

@app.delete("/reports/{report_id}")
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Удалить отчет"""
    report_service = ReportService(db)
    success = report_service.delete_report(report_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted successfully"}

@app.post("/export-pdf")
async def export_pdf(request: Request):
    data = await request.json()
    report_content = data.get("report", "")
    
    # Здесь можно добавить логику экспорта в PDF
    # Пока возвращаем JSON с содержимым
    return {
        "success": True,
        "message": "PDF экспорт будет реализован",
        "content": report_content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
