# Лабораторийн ажил 13: Автомат тест үүсгэлт

Энэ хавтас нь лабораторийн ажлын бүх файлуудыг агуулна.

## Бүтэц

```
examples/tutorial/
├── flaskr/                    # Эх код
│   ├── __init__.py
│   ├── auth.py
│   ├── blog.py
│   └── db.py
├── tests_pynguin/             # Pynguin-ийн үүсгэсэн тестүүд
│   ├── test_auth_pynguin.py
│   ├── test_blog_pynguin.py
│   └── test_db_pynguin.py
├── tests_hypothesis/          # Hypothesis property-based тестүүд
│   ├── test_auth_properties.py
│   └── test_blog_properties.py
├── tests_ai/                  # AI-ийн үүсгэсэн тестүүд
│   ├── test_auth_ai.py
│   ├── test_blog_ai.py
│   └── test_db_ai.py
├── coverage_pynguin/          # Pynguin coverage report (generate хийсний дараа)
├── coverage_hypothesis/       # Hypothesis coverage report
├── coverage_ai/               # AI coverage report
├── REPORT.md                  # Гол тайлан
├── requirements.txt           # Python багцууд
├── run_tests.sh              # Linux/Mac тест ажиллуулах скрипт
└── run_tests.bat             # Windows тест ажиллуулах скрипт
```

## Суулгах

```bash
cd examples/tutorial
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Тест ажиллуулах

### Бүх тестүүдийг нэг дор ажиллуулах:

**Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

**Windows:**
```batch
run_tests.bat
```

### Тусдаа ажиллуулах:

```bash
# Pynguin тест
pytest tests_pynguin --cov=flaskr --cov-report=html:coverage_pynguin -v

# Hypothesis тест
pytest tests_hypothesis --cov=flaskr --cov-report=html:coverage_hypothesis -v

# AI тест
pytest tests_ai --cov=flaskr --cov-report=html:coverage_ai -v
```

## Coverage харах

Coverage report-уудыг HTML форматаар үүсгэсний дараа:

```bash
# Брауз дээр нээх
open coverage_pynguin/html/index.html      # Mac
xdg-open coverage_pynguin/html/index.html  # Linux
start coverage_pynguin/html/index.html     # Windows
```

## Тайлан

Гол тайлан: `REPORT.md`

Тайланд дараах 8 хэсэг багтсан:
1. Сонгосон төсөл ба сонголтын шалтгаан
2. 3 хувилбарын coverage хүснэгт
3. Pynguin-ийн илрүүлсэн алдаа
4. Hypothesis-ээр илэрсэн edge case
5. AI хэрэгслүүдийн жишээ ба үр дүн
6. AI-ийн үүсгэсэн тестүүдийн дутагдал ба засварууд
7. Гар аргаар бичсэн тесттэй харьцуулалт
8. Дүгнэлт

## Асуулт, санал

Хэрэв асуулт байвал REPORT.md файлыг уншина уу.

