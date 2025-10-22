"""
Research stages and prompts for AI Research Assistant
"""

import asyncio
import httpx
from typing import Dict, List, Any
import json
from datetime import datetime

class ResearchStage:
    """Base class for research stages"""
    
    def __init__(self, name: str, description: str, icon: str):
        self.name = name
        self.description = description
        self.icon = icon
        self.status = "pending"  # pending, active, completed, error
        self.progress = 0
        self.result = None
        self.error = None

class ResearchProcessor:
    """Main processor for research stages"""
    
    def __init__(self, config, manager, client_id: str):
        self.config = config
        self.manager = manager
        self.client_id = client_id
        self.stages = []
        self.current_stage = 0
        
    async def send_update(self, stage_name: str, status: str, progress: int, message: str = ""):
        """Send update to client via WebSocket"""
        await self.manager.send_message(self.client_id, {
            "type": "stage_update",
            "stage": stage_name,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _execute_with_retry(self, func, *args, stage_name: str, stage_description: str, max_retries: int = 3):
        """Execute function with retry mechanism"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Попытка {attempt + 1}/{max_retries} для {stage_description}")
                
                if attempt > 0:
                    await self.send_update(stage_name, "active", 0, f"Повторная попытка {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff: 2, 4, 8 seconds
                
                result = await func(*args)
                print(f"✅ {stage_description} успешно выполнено с попытки {attempt + 1}")
                return result
                
            except (httpx.TimeoutException, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_exception = e
                print(f"⏰ Таймаут на попытке {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    await self.send_update(stage_name, "active", 0, f"Таймаут, повторяем через {2 ** (attempt + 1)} сек...")
                else:
                    await self.send_update(stage_name, "error", 0, f"Таймаут после {max_retries} попыток")
                    
            except Exception as e:
                last_exception = e
                print(f"❌ Ошибка на попытке {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    await self.send_update(stage_name, "active", 0, f"Ошибка, повторяем через {2 ** (attempt + 1)} сек...")
                else:
                    await self.send_update(stage_name, "error", 0, f"Ошибка после {max_retries} попыток")
        
        # If all retries failed, raise the last exception
        raise last_exception
    
    async def process_research(self, research_data: Dict[str, Any], research_type: str) -> Dict[str, Any]:
        """Process research through all stages"""
        try:
            print(f"🚀 Начинаем исследование типа: {research_type}")
            print(f"📊 Данные исследования: {research_data}")
            
            # Stage 1: Data Collection
            print("📡 Этап 1: Сбор данных")
            await self.send_update("data_collection", "active", 0, "Собираем данные о рынке...")
            market_data = await self.collect_market_data(research_data, research_type)
            print(f"✅ Данные собраны: {len(market_data.get('companies', []))} компаний")
            
            # Stage 2: Case Analysis
            print("🔍 Этап 2: Анализ кейсов")
            await self.send_update("case_analysis", "active", 0, "Анализируем кейсы...")
            cases = await self.analyze_cases(market_data, research_data, research_type)
            print(f"✅ Кейсы проанализированы: {len(cases)} кейсов")
            
            # Stage 3: Link Verification
            print("🔗 Этап 3: Проверка ссылок")
            await self.send_update("link_verification", "active", 0, "Проверяем ссылки...")
            verified_cases = await self.verify_links(cases)
            print(f"✅ Ссылки проверены: {len(verified_cases)} кейсов")
            
            # Stage 4: Report Generation
            print("📝 Этап 4: Генерация отчета")
            await self.send_update("report_generation", "active", 0, "Генерируем отчет...")
            report = await self.generate_report(verified_cases, research_data, research_type)
            print(f"✅ Отчет готов: {len(report)} символов")
            
            return {
                "success": True,
                "report": report,
                "stages_completed": 4
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Ошибка в процессе исследования: {str(e)}")
            print(f"📋 Детали ошибки:\n{error_details}")
            await self.send_update("error", "error", 0, f"Ошибка: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_details": error_details
            }
    
    async def collect_market_data(self, research_data: Dict[str, Any], research_type: str) -> Dict[str, Any]:
        """Stage 1: Collect market data with retry mechanism"""
        return await self._execute_with_retry(
            self._collect_market_data_internal,
            research_data,
            research_type,
            stage_name="data_collection",
            stage_description="сбора данных"
        )
    
    async def _collect_market_data_internal(self, research_data: Dict[str, Any], research_type: str) -> Dict[str, Any]:
        """Internal method for data collection"""
        await self.send_update("data_collection", "active", 10, "Подготавливаем запрос...")
        
        prompt = self.get_data_collection_prompt(research_data, research_type)
        print(f"📝 Промпт для сбора данных: {len(prompt)} символов")
        
        await self.send_update("data_collection", "active", 30, "Отправляем запрос к ИИ...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            await self.send_update("data_collection", "active", 40, "Выполняем HTTP запрос...")
            api_url = f"{self.config.GEMINI_API_URL}/v1beta/models/{self.config.GEMINI_MODEL}:generateContent"
            print(f"🌐 Отправляем запрос к {api_url}")
            
            response = await client.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.config.GEMINI_API_KEY
                },
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.7
                    }
                }
            )
            
            print(f"📡 Получен ответ: {response.status_code}")
            await self.send_update("data_collection", "active", 70, "Обрабатываем ответ...")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Ответ успешно получен: {len(str(result))} символов")
                await self.send_update("data_collection", "active", 90, "Структурируем данные...")
                
                # Parse the response to extract structured data
                market_data = self.parse_market_data(result, research_type)
                
                await self.send_update("data_collection", "completed", 100, f"Найдено {len(market_data.get('companies', []))} компаний")
                
                return market_data
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                await self.send_update("data_collection", "error", 0, error_msg)
                raise Exception(error_msg)
    
    async def analyze_cases(self, market_data: Dict[str, Any], research_data: Dict[str, Any], research_type: str) -> List[Dict[str, Any]]:
        """Stage 2: Analyze cases with retry mechanism"""
        return await self._execute_with_retry(
            self._analyze_cases_internal,
            market_data,
            research_data,
            research_type,
            stage_name="case_analysis",
            stage_description="анализа кейсов"
        )
    
    async def _analyze_cases_internal(self, market_data: Dict[str, Any], research_data: Dict[str, Any], research_type: str) -> List[Dict[str, Any]]:
        """Internal method for case analysis"""
        await self.send_update("case_analysis", "active", 10, "Подготавливаем анализ кейсов...")
        
        prompt = self.get_case_analysis_prompt(market_data, research_data, research_type)
        
        await self.send_update("case_analysis", "active", 30, "Отправляем запрос на анализ...")
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.config.GEMINI_API_URL}/v1beta/models/{self.config.GEMINI_MODEL}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.config.GEMINI_API_KEY
                },
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.5
                    }
                }
            )
            
            await self.send_update("case_analysis", "active", 70, "Обрабатываем результаты анализа...")
            
            if response.status_code == 200:
                result = response.json()
                await self.send_update("case_analysis", "active", 90, "Структурируем кейсы...")
                
                cases = self.parse_cases(result)
                await self.send_update("case_analysis", "completed", 100, f"Проанализировано {len(cases)} кейсов")
                
                return cases
            else:
                raise Exception(f"API Error: {response.status_code}")
    
    async def verify_links(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 3: Verify and enhance links"""
        await self.send_update("link_verification", "active", 5, "Начинаем проверку ссылок...")
        
        verified_cases = []
        total_cases = len(cases)
        total_links = 0
        working_links = 0
        broken_links = 0
        
        print(f"🔗 Начинаем проверку ссылок для {total_cases} кейсов")
        
        for i, case in enumerate(cases):
            progress = int((i / total_cases) * 90) + 5  # 5-95%
            await self.send_update("link_verification", "active", progress, 
                                 f"Проверяем ссылки для кейса {i+1}/{total_cases}")
            
            print(f"🔍 Проверяем кейс {i+1}: {case.get('title', 'Без названия')}")
            
            verified_case = await self.verify_case_links(case)
            verified_cases.append(verified_case)
            
            # Count links for this case
            case_working = len(verified_case.get('verified_links', []))
            case_broken = len(verified_case.get('broken_links', []))
            case_total = case_working + case_broken
            
            total_links += case_total
            working_links += case_working
            broken_links += case_broken
            
            print(f"📊 Кейс {i+1}: {case_working} рабочих, {case_broken} нерабочих ссылок")
            
            # Small delay to show progress
            await asyncio.sleep(0.3)
        
        await self.send_update("link_verification", "active", 95, "Финализируем проверку...")
        await asyncio.sleep(0.5)  # Small delay for final processing
        
        # Count unique countries from all cases
        unique_countries = set()
        for case in verified_cases:
            if "country" in case and case["country"]:
                # Handle multiple countries in one case (e.g., "Франция, Германия")
                countries = [c.strip() for c in case["country"].split(",") if c.strip()]
                unique_countries.update(countries)
        
        countries_count = len(unique_countries)
        print(f"🌍 Найдено уникальных стран: {countries_count} - {list(unique_countries)}")
        
        # Send countries update
        await self.send_update("link_verification", "active", 98, f"Найдено {countries_count} уникальных стран")
        
        # Print final summary
        print(f"📈 ИТОГИ ПРОВЕРКИ ССЫЛОК:")
        print(f"   Всего кейсов: {total_cases}")
        print(f"   Всего ссылок: {total_links}")
        print(f"   Рабочих ссылок: {working_links}")
        print(f"   Нерабочих ссылок: {broken_links}")
        print(f"   Уникальных стран: {countries_count}")
        if total_links > 0:
            percentage = (working_links / total_links) * 100
            print(f"   Процент рабочих: {percentage:.1f}%")
        
        await self.send_update("link_verification", "completed", 100, f"Проверено {len(verified_cases)} кейсов")
        
        return verified_cases
    
    async def verify_case_links(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Verify links for a single case"""
        verified_case = case.copy()
        
        # Extract links from the case
        links = []
        if "links" in case:
            links = case["links"]
        elif "sources" in case:
            links = case["sources"]
        
        print(f"   🔍 Найдено {len(links)} ссылок для проверки")
        
        # If no links found, ask AI to find more
        if len(links) == 0:
            print(f"   ⚠️ Ссылок не найдено! Запрашиваем у ИИ дополнительные ссылки...")
            additional_links = await self.search_additional_links(case)
            links.extend(additional_links)
            print(f"   🔍 ИИ нашел {len(additional_links)} дополнительных ссылок")
        
        verified_links = []
        broken_links = []
        
        # Check each link
        for i, link in enumerate(links):
            if isinstance(link, str) and link.startswith(('http://', 'https://')):
                print(f"   🔗 Проверяем ссылку {i+1}: {link}")
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.head(link, follow_redirects=True)
                        if response.status_code < 400:
                            print(f"   ✅ Ссылка работает: {response.status_code}")
                            verified_links.append({
                                "url": link,
                                "status": "working",
                                "status_code": response.status_code
                            })
                        else:
                            print(f"   ❌ Ссылка не работает: {response.status_code}")
                            broken_links.append({
                                "url": link,
                                "status": "broken",
                                "status_code": response.status_code
                            })
                except Exception as e:
                    print(f"   ⚠️ Ошибка проверки ссылки: {str(e)}")
                    broken_links.append({
                        "url": link,
                        "status": "error",
                        "error": str(e)
                    })
            else:
                print(f"   ⏭️ Пропускаем невалидную ссылку: {link}")
                # Not a valid URL, skip
                continue
        
        print(f"   📊 Результат: {len(verified_links)} рабочих, {len(broken_links)} нерабочих")
        
        # Update case with verification results
        verified_case["verified_links"] = verified_links
        verified_case["broken_links"] = broken_links
        verified_case["link_status"] = "verified"
        verified_case["verification_timestamp"] = datetime.now().isoformat()
        
        return verified_case
    
    async def search_additional_links(self, case: Dict[str, Any]) -> List[str]:
        """Search for additional links using AI when no links are found"""
        try:
            company_name = case.get('title', case.get('name', 'компания'))
            description = case.get('description', case.get('content', ''))
            
            prompt = f"""
Ты - эксперт по поиску релевантных источников. Для компании "{company_name}" найди ТОЛЬКО 3-5 САМЫХ РЕЛЕВАНТНЫХ и АКТУАЛЬНЫХ ссылок.

ОПИСАНИЕ КОМПАНИИ:
{description}

КРИТЕРИИ ОТБОРА ССЫЛОК:
1. Официальный сайт компании (ОБЯЗАТЕЛЬНО)
2. Самая релевантная страница продукта/функции
3. Один из лучших кейсов использования или отзывов
4. Актуальная новость или пресс-релиз (не старше 2 лет)
5. Профиль в LinkedIn или Crunchbase (если есть)

ВАЖНО:
- ТОЛЬКО 3-5 ссылок, не больше
- Все ссылки должны быть РЕЛЕВАНТНЫМИ и АКТУАЛЬНЫМИ
- Приоритет: официальные источники > кейсы > новости > профили
- Проверь актуальность - ссылки должны работать
- Избегай дублирующих источников

ФОРМАТ ОТВЕТА - ТОЛЬКО СПИСОК ССЫЛОК (3-5 штук):
https://example.com
https://example.com/product/feature
https://example.com/case-study
https://techcrunch.com/example-news
https://linkedin.com/company/example
"""
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.config.GEMINI_API_URL}/v1beta/models/{self.config.GEMINI_MODEL}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.config.GEMINI_API_KEY
                    },
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.3
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Extract links from the response
                    links = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('http://') or line.startswith('https://'):
                            links.append(line)
                    
                    # Limit to 5 most relevant links
                    links = links[:5]
                    
                    print(f"   🔍 ИИ нашел {len(links)} релевантных ссылок: {links}")
                    return links
                else:
                    print(f"   ❌ Ошибка запроса к ИИ: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"   ❌ Ошибка поиска дополнительных ссылок: {str(e)}")
            return []
    
    async def generate_report(self, cases: List[Dict[str, Any]], research_data: Dict[str, Any], research_type: str) -> str:
        """Stage 4: Generate final report with retry mechanism"""
        return await self._execute_with_retry(
            self._generate_report_internal,
            cases,
            research_data,
            research_type,
            stage_name="report_generation",
            stage_description="генерации отчета"
        )
    
    async def _generate_report_internal(self, cases: List[Dict[str, Any]], research_data: Dict[str, Any], research_type: str) -> str:
        """Internal method for report generation"""
        await self.send_update("report_generation", "active", 10, "Подготавливаем данные для отчета...")
        
        prompt = self.get_report_generation_prompt(cases, research_data, research_type)
        
        await self.send_update("report_generation", "active", 30, "Отправляем запрос на генерацию отчета...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.config.GEMINI_API_URL}/v1beta/models/{self.config.GEMINI_MODEL}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.config.GEMINI_API_KEY
                },
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.3
                    }
                }
            )
            
            await self.send_update("report_generation", "active", 70, "Обрабатываем ответ...")
            
            if response.status_code == 200:
                result = response.json()
                await self.send_update("report_generation", "active", 90, "Форматируем отчет...")
                
                report_content = self.extract_report_content(result)
                
                # Don't add verification summary - user doesn't want it
                
                await self.send_update("report_generation", "completed", 100, "Отчет готов!")
                
                return report_content
            else:
                raise Exception(f"API Error: {response.status_code}")
    
    def get_data_collection_prompt(self, research_data: Dict[str, Any], research_type: str) -> str:
        """Get prompt for data collection stage"""
        if research_type == "feature":
            return f"""
Ты — эксперт по поиску и сбору данных о финтех-продуктах.

ЦЕЛЬ: Найти и собрать МАКСИМАЛЬНО ПОДРОБНУЮ информацию о компаниях, которые используют фичу "{research_data.get('research_element', '')}".

ПАРАМЕТРЫ ИССЛЕДОВАНИЯ:
- Продукт: {research_data.get('product_description', '')}
- Сегмент: {research_data.get('segment', '')}
- Элемент: {research_data.get('research_element', '')}
- Бенчмарки: {research_data.get('benchmarks', '')}
- Обязательные игроки: {research_data.get('required_players', '')}
- Обязательные страны: {research_data.get('required_countries', '')}

КРИТИЧЕСКИ ВАЖНО - ПОИСК ССЫЛОК:
1. Найди МИНИМУМ 15-20 компаний
2. Для КАЖДОЙ компании найди МИНИМУМ 8-10 ОФИЦИАЛЬНЫХ ССЫЛОК:
   - Официальный сайт компании
   - Социальные сети (LinkedIn, Twitter, Facebook)
   - Продуктовые страницы и функции
   - Кейсы использования и отзывы
   - Пресс-релизы и новости
   - Информация о финансировании
   - Партнерства и интеграции
   - Достижения и награды
   - Блоги и техническая документация
   - Отзывы клиентов и рейтинги

3. Если ссылок мало - ищи ГЛУБЖЕ:
   - Проверяй LinkedIn, Crunchbase, TechCrunch, Product Hunt
   - Ищи в отраслевых изданиях, блогах, форумах
   - Проверяй актуальность всех ссылок
   - Если не находишь ссылки - ищи альтернативные источники

ВАЖНО:
- НЕ генерируй изображения
- НЕ создавай скриншоты
- Фокусируйся на МАКСИМАЛЬНОМ количестве ссылок
- Используй только проверенные источники
- Группируй по странам/регионам
- Каждая компания должна быть в формате:
  Компания: [название]
  Сайт: [официальный сайт]
  Соцсети: [ссылки на соцсети]
  Продукты: [ссылки на продукты]
  Кейсы: [ссылки на кейсы]
  Новости: [ссылки на новости]
  Финансирование: [ссылки на финансирование]
  Партнерства: [ссылки на партнерства]
  Достижения: [ссылки на достижения]
  Блоги: [ссылки на блоги]
  Отзывы: [ссылки на отзывы]
  Страна: [страна]
  Описание: [краткое описание фичи]

ФОРМАТ ОТВЕТА:
Структурированный список компаний с МАКСИМАЛЬНЫМ количеством ссылок.
"""
        else:  # product research
            return f"""
Ты — эксперт по поиску и сбору данных о финтех-продуктах.

ЦЕЛЬ: Найти и собрать информацию о продуктах с характеристиками "{research_data.get('product_characteristics', '')}".

ПАРАМЕТРЫ ИССЛЕДОВАНИЯ:
- Продукт: {research_data.get('product_description', '')}
- Сегмент: {research_data.get('segment', '')}
- Характеристики: {research_data.get('product_characteristics', '')}
- Обязательные игроки: {research_data.get('required_players', '')}
- Обязательные страны: {research_data.get('required_countries', '')}

ЗАДАЧА:
1. Найди 15-20 продуктов, соответствующих характеристикам
2. Для каждого продукта укажи:
   - Название продукта и компании
   - Страна/регион
   - Тип продукта
   - Ключевые характеристики
   - Официальный сайт
   - Дополнительные источники

ВАЖНО:
- НЕ генерируй изображения
- НЕ создавай скриншоты
- Фокусируйся только на сборе данных
- Используй только проверенные источники
- Каждый продукт должен быть в формате:
  Продукт: [название]
  Компания: [название компании]
  Сайт: [официальный сайт]
  Страна: [страна]
  Характеристики: [ключевые характеристики]

ФОРМАТ ОТВЕТА:
Структурированный список продуктов с базовой информацией.
"""
    
    def get_case_analysis_prompt(self, market_data: Dict[str, Any], research_data: Dict[str, Any], research_type: str) -> str:
        """Get prompt for case analysis stage"""
        if research_type == "feature":
            return f"""
Ты — старший аналитик по финтеху. Проанализируй собранные данные и создай детальные кейсы.

ВХОДНЫЕ ДАННЫЕ:
{json.dumps(market_data, ensure_ascii=False, indent=2)}

ПАРАМЕТРЫ ИССЛЕДОВАНИЯ:
- Продукт: {research_data.get('product_description', '')}
- Сегмент: {research_data.get('segment', '')}
- Элемент: {research_data.get('research_element', '')}

КРИТИЧЕСКИ ВАЖНО - МАКСИМАЛЬНОЕ КОЛИЧЕСТВО ССЫЛОК:
1. Для КАЖДОГО кейса найди МИНИМУМ 5-7 ПОДТВЕРЖДАЮЩИХ ССЫЛОК
2. Если ссылок мало - ищи ГЛУБЖЕ в исходных данных
3. Проверяй все найденные ссылки на актуальность
4. Добавляй ссылки на:
   - Официальные страницы продуктов
   - Техническую документацию
   - Кейсы использования
   - Отзывы клиентов
   - Пресс-релизы и новости
   - Партнерские интеграции
   - Достижения и награды

ЗАДАЧА:
Создай 10-12 детальных кейсов по шаблону:

**Кейс [номер]: [Название компании]**

**Краткое описание:** [1-2 предложения]

**Страна:** [страна регистрации]

**Подробное описание фичи:**
- Как работает фича
- Где в пользовательском пути
- Для кого предназначена
- Какие триггеры
- Метрики/результаты (если есть)

**Источники (МИНИМУМ 5-7 ссылок):**
- [официальная ссылка 1]
- [продуктовая ссылка 2]
- [кейс использования 3]
- [техническая документация 4]
- [отзыв клиента 5]
- [новость/пресс-релиз 6]
- [партнерство/интеграция 7]


ВАЖНО:
- НЕ генерируй изображения
- НЕ создавай скриншоты
- Каждый кейс должен быть уникальным
- Все ссылки должны быть рабочими
- Указывай конкретные даты
- Фокусируйся на применимости к нашему контексту
- Используй только текстовое описание
"""
        else:  # product research
            return f"""
Ты — старший аналитик по финтеху. Проанализируй собранные данные и создай детальные кейсы продуктов.

ВХОДНЫЕ ДАННЫЕ:
{json.dumps(market_data, ensure_ascii=False, indent=2)}

ПАРАМЕТРЫ ИССЛЕДОВАНИЯ:
- Продукт: {research_data.get('product_description', '')}
- Сегмент: {research_data.get('segment', '')}
- Характеристики: {research_data.get('product_characteristics', '')}

ЗАДАЧА:
Создай 10-12 детальных кейсов продуктов по шаблону:

**Кейс [номер]: [Название продукта]**

**Компания:** [название компании]

**Краткое описание:** [1-2 предложения о продукте]

**Страна:** [страна регистрации]

**Ключевые характеристики:**
- [характеристика 1]
- [характеристика 2]
- [характеристика 3]

**Подробное описание:**
- Функциональность
- Целевая аудитория
- Уникальные особенности
- Результаты/метрики (если есть)

**Источники:**
- [ссылка 1]
- [ссылка 2]
- [ссылка 3]


ВАЖНО:
- НЕ генерируй изображения
- НЕ создавай скриншоты
- Каждый кейс должен быть уникальным
- Все ссылки должны быть рабочими
- Указывай конкретные даты
- Используй только текстовое описание
"""
    
    def get_report_generation_prompt(self, cases: List[Dict[str, Any]], research_data: Dict[str, Any], research_type: str) -> str:
        """Get prompt for final report generation"""
        if research_type == "feature":
            return f"""
Ты — старший аналитик по финтеху. Создай финальный отчет на основе проанализированных кейсов.

ПРОАНАЛИЗИРОВАННЫЕ КЕЙСЫ:
{json.dumps(cases, ensure_ascii=False, indent=2)}

ПАРАМЕТРЫ ИССЛЕДОВАНИЯ:
- Продукт: {research_data.get('product_description', '')}
- Сегмент: {research_data.get('segment', '')}
- Элемент: {research_data.get('research_element', '')}

СОЗДАЙ ОТЧЕТ В СЛЕДУЮЩЕМ ФОРМАТЕ:

# Отчет по исследованию фичи: {research_data.get('research_element', '')}

## Executive Summary
[Краткое резюме на 5-7 пунктов]

## Анализ кейсов
[Детальное описание каждого кейса с таблицей]

### Таблица сравнения кейсов
| № | Компания | Страна | Описание фичи | Источники |
|---|----------|--------|---------------|-----------|-----------------|
| 1 | [название] | [страна] | [описание] | [ссылки] |
| 2 | [название] | [страна] | [описание] | [ссылки] |
| ... | ... | ... | ... | ... |

## Применимость к нашему продукту
[Анализ применимости с конкретными рекомендациями]

## План внедрения
[Пошаговый план внедрения с оценкой сложности]

## Риски и ограничения
[Потенциальные риски и способы их минимизации]

КРИТИЧЕСКИ ВАЖНО - МАКСИМАЛЬНОЕ КОЛИЧЕСТВО ССЫЛОК:
1. В КАЖДОЙ таблице должно быть МИНИМУМ 3-5 ссылок на компанию
2. Все ссылки должны быть ПРОВЕРЕННЫМИ и АКТУАЛЬНЫМИ
3. Если ссылок мало - ищи ГЛУБЖЕ в исходных данных
4. Добавляй ссылки на:
   - Официальные сайты компаний
   - Продуктовые страницы
   - Кейсы использования
   - Техническую документацию
   - Отзывы клиентов
   - Пресс-релизы и новости
   - Партнерские интеграции

ВАЖНО:
- НЕ генерируй изображения
- НЕ создавай скриншоты
- Используй только таблицы для структурирования данных
- Все ссылки должны быть проверенными и актуальными
- Фокусируйся на практической применимости
- Используй маркдаун форматирование
- Только текстовый контент
- МАКСИМАЛЬНОЕ количество ссылок в каждой таблице
"""
        else:  # product research
            return f"""
Ты — старший аналитик по финтеху. Создай финальный отчет на основе проанализированных продуктов.

ПРОАНАЛИЗИРОВАННЫЕ ПРОДУКТЫ:
{json.dumps(cases, ensure_ascii=False, indent=2)}

ПАРАМЕТРЫ ИССЛЕДОВАНИЯ:
- Продукт: {research_data.get('product_description', '')}
- Сегмент: {research_data.get('segment', '')}
- Характеристики: {research_data.get('product_characteristics', '')}

СОЗДАЙ ОТЧЕТ В СЛЕДУЮЩЕМ ФОРМАТЕ:

# Отчет по исследованию продукта: {research_data.get('product_characteristics', '')}

## Executive Summary
[Краткое резюме на 5-7 пунктов]

## Анализ продуктов
[Детальное описание каждого продукта с таблицей]

### Таблица сравнения продуктов
| № | Продукт | Компания | Страна | Характеристики | Источники |
|---|---------|----------|--------|----------------|-----------|-----------------|
| 1 | [название] | [компания] | [страна] | [характеристики] | [ссылки] |
| 2 | [название] | [компания] | [страна] | [характеристики] | [ссылки] |
| ... | ... | ... | ... | ... | ... |

## Рыночные тренды
[Анализ трендов и паттернов]

## Рекомендации
[Конкретные рекомендации для нашего продукта]

## План развития
[Пошаговый план развития продукта]

КРИТИЧЕСКИ ВАЖНО - МАКСИМАЛЬНОЕ КОЛИЧЕСТВО ССЫЛОК:
1. В КАЖДОЙ таблице должно быть МИНИМУМ 3-5 ссылок на продукт
2. Все ссылки должны быть ПРОВЕРЕННЫМИ и АКТУАЛЬНЫМИ
3. Если ссылок мало - ищи ГЛУБЖЕ в исходных данных
4. Добавляй ссылки на:
   - Официальные сайты продуктов
   - Продуктовые страницы
   - Кейсы использования
   - Техническую документацию
   - Отзывы клиентов
   - Пресс-релизы и новости
   - Партнерские интеграции

ВАЖНО:
- НЕ генерируй изображения
- НЕ создавай скриншоты
- Используй только таблицы для структурирования данных
- Все ссылки должны быть проверенными и актуальными
- Фокусируйся на практической применимости
- Используй маркдаун форматирование
- Только текстовый контент
- МАКСИМАЛЬНОЕ количество ссылок в каждой таблице
"""
    
    def parse_market_data(self, api_response: Dict[str, Any], research_type: str) -> Dict[str, Any]:
        """Parse market data from API response"""
        try:
            if "candidates" in api_response and len(api_response["candidates"]) > 0:
                content = api_response["candidates"][0]["content"]["parts"][0]["text"]
                
                # Parse the content to extract structured data
                companies = self.extract_companies_from_text(content)
                
                return {
                    "raw_content": content,
                    "companies": companies,
                    "research_type": research_type,
                    "timestamp": datetime.now().isoformat(),
                    "total_found": len(companies)
                }
            else:
                return {
                    "raw_content": "No data found",
                    "companies": [],
                    "research_type": research_type,
                    "timestamp": datetime.now().isoformat(),
                    "total_found": 0
                }
        except Exception as e:
            return {
                "raw_content": f"Error parsing data: {str(e)}",
                "companies": [],
                "research_type": research_type,
                "timestamp": datetime.now().isoformat(),
                "total_found": 0
            }
    
    def extract_companies_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract company information from text"""
        companies = []
        lines = text.split('\n')
        
        current_company = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_company:
                    companies.append(current_company)
                    current_company = {}
                continue
                
            # Look for company patterns
            if any(keyword in line.lower() for keyword in ['компания:', 'company:', 'название:', 'name:']):
                if current_company:
                    companies.append(current_company)
                current_company = {"name": line.split(':', 1)[1].strip() if ':' in line else line}
            elif any(keyword in line.lower() for keyword in ['сайт:', 'website:', 'url:']):
                if current_company:
                    current_company["website"] = line.split(':', 1)[1].strip() if ':' in line else line
            elif any(keyword in line.lower() for keyword in ['страна:', 'country:']):
                if current_company:
                    current_company["country"] = line.split(':', 1)[1].strip() if ':' in line else line
            elif line.startswith('http'):
                if current_company:
                    if "links" not in current_company:
                        current_company["links"] = []
                    current_company["links"].append(line)
        
        if current_company:
            companies.append(current_company)
            
        return companies
    
    def parse_cases(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse cases from API response"""
        try:
            if "candidates" in api_response and len(api_response["candidates"]) > 0:
                content = api_response["candidates"][0]["content"]["parts"][0]["text"]
                
                # Parse the content to extract case information
                cases = self.extract_cases_from_text(content)
                
                return cases
            else:
                return []
        except Exception as e:
            return []
    
    def extract_cases_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract case information from text"""
        cases = []
        lines = text.split('\n')
        
        current_case = {}
        case_number = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for case patterns
            if line.startswith(f'**Кейс {case_number}') or line.startswith(f'Кейс {case_number}'):
                if current_case:
                    cases.append(current_case)
                current_case = {
                    "number": case_number,
                    "title": line.replace('**', '').replace('*', '').strip()
                }
                case_number += 1
            elif line.startswith('**Компания:') or line.startswith('Компания:'):
                if current_case:
                    current_case["company"] = line.split(':', 1)[1].strip() if ':' in line else line
            elif line.startswith('**Страна:') or line.startswith('Страна:'):
                if current_case:
                    current_case["country"] = line.split(':', 1)[1].strip() if ':' in line else line
            elif line.startswith('**Источники:') or line.startswith('Источники:'):
                if current_case:
                    current_case["sources"] = []
            elif line.startswith('http'):
                if current_case:
                    if "sources" not in current_case:
                        current_case["sources"] = []
                    current_case["sources"].append(line)
            elif current_case and line and not line.startswith('**'):
                # This is likely description content
                if "description" not in current_case:
                    current_case["description"] = line
                else:
                    current_case["description"] += " " + line
        
        if current_case:
            cases.append(current_case)
            
        return cases
    
    def add_verification_summary(self, report_content: str, cases: List[Dict[str, Any]]) -> str:
        """Add verification summary to the report"""
        total_links = 0
        working_links = 0
        broken_links = 0
        
        for case in cases:
            if "verified_links" in case:
                total_links += len(case["verified_links"])
                working_links += len([link for link in case["verified_links"] if link.get("status") == "working"])
            if "broken_links" in case:
                broken_links += len(case["broken_links"])
        
        percentage = (working_links/total_links*100) if total_links > 0 else 0
        
        verification_summary = f"""

## Сводка проверки ссылок

- **Всего ссылок проверено:** {total_links}
- **Рабочих ссылок:** {working_links}
- **Нерабочих ссылок:** {broken_links}
- **Процент рабочих ссылок:** {percentage:.1f}%

*Все ссылки были проверены на доступность и актуальность.*
"""
        
        return report_content + verification_summary
    
    def extract_report_content(self, api_response: Dict[str, Any]) -> str:
        """Extract report content from API response"""
        try:
            if "candidates" in api_response and len(api_response["candidates"]) > 0:
                content = api_response["candidates"][0]["content"]["parts"][0]["text"]
                return content
            else:
                return "Ошибка при генерации отчета"
        except Exception as e:
            return f"Ошибка при обработке ответа: {str(e)}"
