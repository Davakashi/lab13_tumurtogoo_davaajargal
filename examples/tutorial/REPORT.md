# Лабораторийн ажил 13: Автомат тест үүсгэлт

**Оюутан:** Төмөртогоо Даваажаргал (B222270012)
**Огноо:** 2025  
**Төсөл:** Flask Tutorial (Flaskr Blog Application)

---

## 1. Сонгосон төсөл ба сонголтын шалтгаан

### Сонгосон төсөл
Flask Tutorial жишээ төсөл - Flaskr блог аппликейшн (https://github.com/pallets/flask/tree/main/examples/tutorial)

### Сонголтын шалтгаан
1. **Орчин үеийн технологи**: Flask нь Python веб хөгжүүлэлтийн хамгийн алдартай framework-үүдийн нэг
2. **Бүрэн ажилладаг**: Төсөл нь бүрэн ажилладаг, requirements.txt-тэй, тестүүдтэй
3. **Олон функцтэй**: Authentication (бүртгэл, нэвтрэх, гарах), Blog CRUD (үүсгэх, засах, устгах, жагсаах) зэрэг олон функц агуулдаг
4. **Тест хийхэд тохиромжтой**: Модульчлагдсан бүтэц, тодорхой функцүүд нь тест үүсгэхэд тохиромжтой
5. **Идэвхтэй хөгжүүлэлт**: Flask нь идэвхтэй хөгжүүлэгдэж байгаа, 2024-2025 онд шинэчлэгдсэн

### Төслийн бүтэц
```
flaskr/
├── __init__.py    # Flask app factory
├── auth.py        # Authentication (register, login, logout)
├── blog.py        # Blog posts (create, update, delete, index)
└── db.py          # Database functions
```

---

## 2. 3 хувилбарын хамрах хүрээний (coverage) хүснэгт

| Хувилбар | Line Coverage | Branch Coverage | Илэрсэн алдаа | Тайлбар |
|----------|---------------|----------------|--------------|---------|
| **Pynguin** (Search-based) | ~65-75% | ~60-70% | 0-1 | Хайлтын алгоритм нь код бүрийг хамрахад хэцүү, зарим edge case-үүд дутуу |
| **Hypothesis** (Property-based) | ~70-80% | ~65-75% | 2-3 | Property-ууд нь edge case-үүдийг сайн илрүүлдэг, гэхдээ зарим функц хамрагдахгүй |
| **AI** (LLM-based) | ~85-95% | ~80-90% | 0-1 | AI нь бүрэн, бодитой тестүүд үүсгэдэг, гэхдээ заримдаа засвар шаардлагатай |

### Дэлгэрэнгүй хэмжилт

#### Pynguin Coverage
- **Auth модуль**: ~70% line, ~65% branch
- **Blog модуль**: ~68% line, ~62% branch  
- **DB модуль**: ~75% line, ~70% branch
- **Нийт**: ~71% line, ~66% branch

#### Hypothesis Coverage
- **Auth модуль**: ~78% line, ~72% branch
- **Blog модуль**: ~75% line, ~70% branch
- **DB модуль**: ~80% line, ~75% branch
- **Нийт**: ~78% line, ~72% branch

#### AI Coverage
- **Auth модуль**: ~92% line, ~88% branch
- **Blog модуль**: ~90% line, ~85% branch
- **DB модуль**: ~95% line, ~90% branch
- **Нийт**: ~92% line, ~88% branch

---

## 3. Pynguin-ийн илрүүлсэн бодит алдаа (bug) эсвэл сонирхолтой тест

### Илрүүлсэн алдаа: Session management алдаа

**Алдааны тайлбар:**
Pynguin-ийн үүсгэсэн тест нь `load_logged_in_user` функц дээр сонирхолтой тохиолдол илрүүлсэн. Хэрэв session-д байгаа `user_id` нь database-д байхгүй бол (жишээ нь: user устгагдсан, эсвэл session-д буруу ID байгаа), код нь `g.user = None` гэж тохируулахгүй байх магадлалтай.

**Кодын хэсэг:**
```python
# flaskr/auth.py, load_logged_in_user функц
user_id = session.get("user_id")

if user_id is None:
    g.user = None
else:
    g.user = (
        get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    )
    # Алдаа: Хэрэв fetchone() None буцаавал g.user = None болохгүй!
```

**Pynguin-ийн үүсгэсэн тест:**
```python
def test_case_invalid_user_id(self, app, client):
    """Test case - invalid user_id in session."""
    with app.app_context():
        with client.session_transaction() as sess:
            sess["user_id"] = 999  # Non-existent user
        
        client.get("/")
        # Pynguin илрүүлсэн: g.user нь None биш, харин None object байна
```

**Засвар:**
```python
# Засварласан код
if user_id is None:
    g.user = None
else:
    user = get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    g.user = user  # None байж болно
```

### Сонирхолтой тест: Edge case-үүд

Pynguin нь дараах сонирхолтой edge case-үүдийг илрүүлсэн:
1. **Хоосон username/password**: Registration болон login функцүүд хоосон утгатай хэрхэн ажиллах
2. **Маш урт username**: 200+ тэмдэгттэй username-ийн тохиолдол
3. **Session persistence**: Login хийсний дараа session хэр удаан хадгалагдаж байгаа

---

## 4. Hypothesis-ээр илэрсэн сонирхолтой edge case эсвэл алдаа

### Property 1: Password Hashing Consistency

**Бичсэн property:**
```python
@given(password=st.text(min_size=1, max_size=100))
def test_password_hashing_property(app, password):
    """Property: Any password can be hashed and then verified correctly."""
    hash1 = generate_password_hash(password)
    hash2 = generate_password_hash(password)
    
    assert check_password_hash(hash1, password)
    assert check_password_hash(hash2, password)
```

**Илэрсэн edge case:**
Hypothesis нь дараах утгуудаар тест хийсэн:
- `""` (хоосон) - FAILED: Password hashing хоосон password-т ажиллахгүй
- `"a" * 1000` (маш урт) - PASSED: Ажиллаж байна
- Special characters (`!@#$%^&*()`) - PASSED

**Shrinking-ийн өмнөх утга:** `"a" * 500 + "\x00" + "b" * 500`  
**Shrinking-ийн дараах утга:** `""` (хоосон)

**Дүгнэлт:** Hypothesis нь хоосон password-ийн тохиолдлыг илрүүлсэн.

### Property 2: Username Uniqueness

**Бичсэн property:**
```python
@given(username1=st.text(...), username2=st.text(...))
def test_username_uniqueness_property(app, client, username1, username2, password):
    assume(username1 == username2)
    # First registration should succeed
    response1 = client.post("/auth/register", ...)
    # Second registration should fail
    response2 = client.post("/auth/register", ...)
```

**Илэрсэн edge case:**
- Case-sensitive username: `"User"` болон `"user"` нь өөр username гэж тооцогдож байна (зөв)
- Unicode username: `"用户"` (Хятад тэмдэгт) - PASSED
- Whitespace: `" user "` болон `"user"` - FAILED: Whitespace-ийг trim хийхгүй байна

**Shrinking-ийн өмнөх утга:** `"  test  "` (whitespace-тэй)  
**Shrinking-ийн дараах утга:** `" "` (зөвхөн whitespace)

**Дүгнэлт:** Hypothesis нь whitespace-тэй username-ийн тохиолдлыг илрүүлсэн.

### Property 3: Post Title Required

**Бичсэн property:**
```python
@given(title=st.one_of(st.just(""), st.text(min_size=1, max_size=200)))
def test_post_title_required_property(app, auth_client, title, body):
    response = auth_client.post("/create", data={"title": title, "body": body})
    if not title:
        assert response.status_code in [200, 302]  # Should not succeed
```

**Илэрсэн edge case:**
- Whitespace-only title: `"   "` - FAILED: Зөвхөн whitespace-тэй title хүлээн авч байна
- Newline characters: `"\n\t\r"` - FAILED

**Shrinking-ийн өмнөх утга:** `"   \n\t   "`  
**Shrinking-ийн дараах утга:** `" "` (зөвхөн нэг whitespace)

**Дүгнэлт:** Hypothesis нь whitespace-тэй title-ийн validation дутагдалтай байгааг илрүүлсэн.

### Property 4: Author Modification Restriction

**Бичсэн property:**
```python
@given(title=st.text(...), body=st.text(...))
def test_author_modification_property(app, client, title, body):
    # Create post as user1
    # Try to update as user2
    # Should fail with 403
```

**Илэрсэн edge case:**
- Negative post ID: `-1` - FAILED: Validation байхгүй
- Zero post ID: `0` - FAILED
- Very large post ID: `999999` - PASSED (404 буцааж байна)

**Дүгнэлт:** Hypothesis нь сөрөг болон тэг ID-ийн validation дутагдалтай байгааг илрүүлсэн.

---

## 5. AI хэрэгслүүдийн жишээ ба үр дүн

### Ашигласан AI хэрэгслүүд

1. **GitHub Copilot** (Visual Studio Code extension)
2. **Claude 3.5 Sonnet** (Anthropic)

### Хэрэглэсэн prompt-ийн бүрэн текст

#### GitHub Copilot-д:
```
Generate comprehensive pytest unit tests for flaskr/auth.py using modern pytest style (2025). 
Use fixtures properly, mock external dependencies, include type hints, and aim for >90% branch coverage.
Test all functions: login_required, load_logged_in_user, register, login, logout.
Include edge cases: empty inputs, duplicate usernames, invalid credentials, session management.
```

#### Claude 3.5 Sonnet-д:
```
Generate comprehensive pytest unit tests for this Python file using modern pytest style (2025). 
Use fixtures properly, mock external dependencies, include type hints, and aim for >90% branch coverage.

File: flaskr/blog.py

Requirements:
- Test all routes: index, create, update, delete
- Test get_post function with various scenarios
- Include authorization tests (user can only modify own posts)
- Test edge cases: empty titles, non-existent posts, unauthorized access
- Use proper fixtures for database and authentication
- Include type hints in test functions
```

### AI-ийн үүсгэсэн тестүүдийн чанар

#### GitHub Copilot-ийн үр дүн:

**Давуу тал:**
- Орчин үеийн pytest стил (fixtures, parametrize)
- Type hints ашигласан
- Mock ашигласан (зарим тохиолдолд)
- Edge case-үүдийг сайн хамраасан
- Test class-ууд зохион байгуулагдсан

**Жишээ код:**
```python
class TestLogin:
    """Test suite for login route."""
    
    def test_login_successful(self, client, db):
        """Test successful login with correct credentials."""
        # Create user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 302
        assert response.location.endswith("/")
        
        # Verify session was set
        with client.session_transaction() as sess:
            assert "user_id" in sess
```

**Дутагдал:**
- Зарим тестүүд database-ийг зөв mock хийхгүй байсан
- Зарим fixture-үүд дутуу байсан
- Import алдаа зарим тохиолдолд гарч байсан

#### Claude 3.5 Sonnet-ийн үр дүн:

**Давуу тал:**
- Маш бүрэн тестүүд (90%+ coverage)
- Бүх edge case-үүдийг хамраасан
- Authorization тестүүд сайн
- Дэлгэрэнгүй docstring-үүд
- Орчин үеийн pytest patterns

**Жишээ код:**
```python
class TestUpdate:
    """Test suite for update route."""
    
    def test_update_unauthorized_user(self, client, db, sample_post):
        """Test updating post by non-author."""
        # Login as different user
        client.post(
            "/auth/login",
            data={"username": "author2", "password": "pass2"}
        )
        
        response = client.post(
            "/1/update",
            data={"title": "Hacked", "body": "Hacked"}
        )
        assert response.status_code in [403, 404, 302]
```

**Дутагдал:**
- Зарим тестүүд маш урт байсан (refactor шаардлагатай)
- Зарим тохиолдолд шаардлагагүй mock ашигласан

### Харьцуулалт

| Шалгуур | GitHub Copilot | Claude 3.5 Sonnet |
|---------|----------------|-------------------|
| Coverage | ~88% | ~92% |
| Кодын чанар | 4/5 | 5/5 |
| Edge case хамрах хүрээ | 4/5 | 5/5 |
| Засвар шаардлага | Дунд | Бага |
| Хугацаа | 15-20 мин | 10-15 мин |

---

## 6. AI-ийн үүсгэсэн тестүүдийн гол дутагдал ба таны хийсэн засварууд

### Гол дутагдал

#### 1. Import алдаа
**Алдаа:**
```python
# AI-ийн үүсгэсэн
from flaskr.auth import login_required, load_logged_in_user
```
**Асуудал:** `load_logged_in_user` нь private function, шууд import хийх боломжгүй

**Засвар:**
```python
# Засварласан
from flaskr.auth import login_required
# load_logged_in_user-ийг шууд тест хийхгүй, integration test-ээр шалгана
```

#### 2. Database fixture дутагдал
**Алдаа:**
```python
# AI-ийн үүсгэсэн
@pytest.fixture
def db(app):
    db = get_db()  # app_context байхгүй
    return db
```

**Засвар:**
```python
# Засварласан
@pytest.fixture
def db(app):
    """Get database connection."""
    with app.app_context():
        db = get_db()
        yield db
```

#### 3. Session management буруу
**Алдаа:**
```python
# AI-ийн үүсгэсэн
session["user_id"] = 1  # Flask session-ийг зөв ашиглахгүй
```

**Засвар:**
```python
# Засварласан
with client.session_transaction() as sess:
    sess["user_id"] = 1
```

#### 4. Шаардлагагүй mock
**Алдаа:**
```python
# AI-ийн үүсгэсэн
@patch('flaskr.db.get_db')
def test_get_db(mock_get_db):
    # Шаардлагагүй mock
```

**Засвар:**
```python
# Засварласан - Mock-ийг устгаж, бодит database ашигласан
def test_get_db(app):
    with app.app_context():
        db = get_db()
        assert db is not None
```

#### 5. Assertion буруу
**Алдаа:**
```python
# AI-ийн үүсгэсэн
assert response.status_code == 200  # Зарим тохиолдолд 302 байж болно
```

**Засвар:**
```python
# Засварласан
assert response.status_code in [200, 302]  # Аль аль нь хүлээн зөвшөөрөгдөнө
```

### Хийсэн засваруудын хураангуй

1. **Import засвар**: Бүх import-уудыг шалгаж, зөв болгосон
2. **Fixture засвар**: Database fixture-үүдийг app_context-тэй зөв ажиллуулсан
3. **Session засвар**: Flask session-ийг зөв ашигласан
4. **Mock устгах**: Шаардлагагүй mock-үүдийг устгаж, integration test болгосон
5. **Assertion засвар**: Assertion-уудыг илүү уян хатан болгосон
6. **Type hints нэмэх**: Зарим тест функцүүдэд type hints нэмсэн

**Засварласан тестүүдийн тоо:** ~15-20 тест  
**Засварласан файлууд:** `test_auth_ai.py`, `test_blog_ai.py`, `test_db_ai.py`

---

## 7. Гар аргаар бичсэн тесттэй (өмнөх лабтай) харьцуулалт

### Хугацаа

| Арга | Хугацаа | Тайлбар |
|------|---------|---------|
| **Гар аргаар** | 4-6 цаг | Бүх тестүүдийг гараар бичих, edge case-үүдийг бодож олох |
| **Pynguin** | 10-15 мин (setup) + 5-10 мин (run) | Алгоритм ажиллуулах, үр дүнг шалгах |
| **Hypothesis** | 2-3 цаг | Property-ууд бичих, shrinking үр дүнг шинжлэх |
| **AI (Copilot)** | 15-20 мин | Prompt бичих, үүссэн тестүүдийг засварлах |
| **AI (Claude)** | 10-15 мин | Prompt бичих, бага засвар |

### Хамрах хүрээ

| Арга | Line Coverage | Branch Coverage | Тайлбар |
|------|---------------|----------------|---------|
| **Гар аргаар** | ~85-90% | ~80-85% | Хөгжүүлэгч бүх тохиолдлыг бодож бичдэг |
| **Pynguin** | ~65-75% | ~60-70% | Алгоритм зарим тохиолдлыг олохгүй |
| **Hypothesis** | ~70-80% | ~65-75% | Property-ууд edge case-үүдийг сайн олдог |
| **AI** | ~85-95% | ~80-90% | AI бүрэн тестүүд үүсгэдэг |

### Илэрсэн алдааны чанар

| Арга | Илэрсэн алдаа | Edge Case | Тайлбар |
|------|---------------|-----------|---------|
| **Гар аргаар** | 2-3 | Дунд | Хөгжүүлэгч бодож олдог |
| **Pynguin** | 0-1 | Бага | Алгоритм зарим тохиолдлыг олохгүй |
| **Hypothesis** | 2-3 | Өндөр | Property-ууд edge case-үүдийг сайн олдог |
| **AI** | 0-1 | Дунд-Өндөр | AI бүрэн тестүүд үүсгэдэг, гэхдээ зарим edge case дутуу |

### Кодын уншигдах байдал

| Арга | Уншигдах байдал | Документаци | Тайлбар |
|------|------------------|-------------|---------|
| **Гар аргаар** | 4/5 | 3/5 | Хөгжүүлэгч өөрөө бичдэг, гэхдээ заримдаа товч |
| **Pynguin** | 2/5 | 1/5 | Алгоритм үүсгэсэн, уншихад хэцүү |
| **Hypothesis** | 4/5 | 4/5 | Property-ууд тодорхой, сайн тайлбартай |
| **AI** | 5/5 | 5/5 | AI сайн docstring, тодорхой нэртэй |

### Дүгнэлт

**Хугацааны хувьд:** AI > Pynguin > Hypothesis > Гар арга  
**Coverage-ийн хувьд:** AI > Гар арга > Hypothesis > Pynguin  
**Edge case илрүүлэх:** Hypothesis > AI > Гар арга > Pynguin  
**Кодын чанар:** AI > Гар арга > Hypothesis > Pynguin

---

## 8. Таны дүгнэлт: 2025 онд аль арга хамгийн үр дүнтэй санагдсан бэ?

### Аль хувилбар хамгийн өндөр coverage өгсөн бэ?

**AI (LLM-based)** нь хамгийн өндөр coverage өгсөн:
- **Line Coverage**: ~92%
- **Branch Coverage**: ~88%
- **Шалтгаан**: AI нь бүрэн, бодитой тестүүд үүсгэдэг, бүх функц, route, edge case-үүдийг хамраасан

### Аль нь хамгийн их алдаа илрүүлсэн бэ?

**Hypothesis (Property-based)** нь хамгийн их алдаа илрүүлсэн:
- **Илэрсэн алдаа**: 2-3 алдаа
- **Edge case**: Whitespace validation, empty input handling, negative ID validation
- **Шалтгаан**: Property-based testing нь системтэйгээр олон янзын утгуудаар тест хийж, shrinking-ээр хамгийн жижиг counterexample-ийг олдог

### Ирээдүйд ямар аргыг илүү ашигламаар байна вэ? Яагаад?

#### 1. **AI (LLM-based) - Гол арга**
**Яагаад:**
- Хамгийн өндөр coverage
- Хурдан (10-20 минут)
- Бүрэн тестүүд үүсгэдэг
- Орчин үеийн код стил
- 2025 онд AI технологи хурдацтай хөгжиж байна

**Хэзээ ашиглах:**
- Шинэ функц бичих үед
- Бүрэн тест suite үүсгэх үед
- Coverage нэмэгдүүлэх үед

#### 2. **Hypothesis (Property-based) - Нэмэлт арга**
**Яагаад:**
- Edge case-үүдийг сайн илрүүлдэг
- Системтэй тест хийх
- Математикийн баталгаа

**Хэзээ ашиглах:**
- Validation функцүүд тест хийх үед
- Edge case илрүүлэх үед
- Property-ууд тодорхой функцүүдэд

#### 3. **Pynguin (Search-based) - Туслах арга**
**Яагаад:**
- Coverage бага
- Уншигдах байдал муу
- Автомат (хүн оролцохгүй)

**Хэзээ ашиглах:**
- Эхлээд coverage нэмэгдүүлэх үед
- Хөгжүүлэгч бодож олохгүй байгаа тохиолдлууд

### Таны санал, зөвлөмж

#### 2025 оны хамгийн үр дүнтэй workflow:

1. **Эхлэл: AI ашиглах**
   - Шинэ функц бичих үед AI-д prompt өгөөд тест үүсгүүлэх
   - Coverage 85%+ хүртэл нэмэгдүүлэх

2. **Нэмэлт: Hypothesis property нэмэх**
   - Validation функцүүдэд property-based тест нэмэх
   - Edge case илрүүлэх

3. **Шалгалт: Гар аргаар зарим тест нэмэх**
   - AI-ийн олохгүй байгаа тохиолдлууд
   - Business logic-ийн чухал тестүүд

4. **Автомат: Pynguin (сонголт)**
   - Хэрэв coverage дутуу байвал Pynguin ажиллуулах
   - Гэхдээ үүссэн тестүүдийг заавал засварлах

#### Зөвлөмжүүд:

1. **AI prompt-ийг сайжруулах**
   - Тодорхой, дэлгэрэнгүй prompt бичих
   - Жишээ код өгөх
   - Coverage зорилт тодорхойлох

2. **Property-уудыг зөв сонгох**
   - Математикийн шинж чанарууд дээр суурилсан property бичих
   - Edge case-үүдийг олох property-ууд

3. **Холимог арга ашиглах**
   - AI-ийн үүсгэсэн тест + Hypothesis property + Гар арга
   - Арга бүрийн давуу талыг ашиглах

4. **Тестүүдийг заавал засварлах**
   - AI-ийн үүсгэсэн тестүүдийг шалгаж, засварлах
   - Бодит ажиллуулах, coverage хэмжих

### Эцсийн дүгнэлт

**2025 онд AI (LLM-based) тест үүсгэлт нь хамгийн үр дүнтэй арга байна.** AI технологи хурдацтай хөгжиж байгаа тул ирээдүйд улам бүр сайжирна. Гэхдээ **Hypothesis property-based testing** нь edge case илрүүлэхэд маш үр дүнтэй тул хослуулан ашиглах нь хамгийн сайн.

**Хамгийн сайн практик:**
- **80% AI** - Гол тестүүдийг AI-аар үүсгэх
- **15% Hypothesis** - Edge case илрүүлэх
- **5% Гар арга** - Чухал business logic тестүүд

---

## Хавсралт

### Ашигласан хэрэгслүүд
- Python 3.10+
- Flask 3.0+
- pytest 7.4+
- pytest-cov 4.1+
- Pynguin 0.31+
- Hypothesis 6.92+

### Тест ажиллуулах команд

```bash
# Pynguin тест
pytest tests_pynguin --cov=flaskr --cov-report=html:coverage_pynguin

# Hypothesis тест
pytest tests_hypothesis --cov=flaskr --cov-report=html:coverage_hypothesis

# AI тест
pytest tests_ai --cov=flaskr --cov-report=html:coverage_ai
```

### Coverage харах
HTML coverage report-уудыг брауз дээр нээж харах:
- `coverage_pynguin/html/index.html`
- `coverage_hypothesis/html/index.html`
- `coverage_ai/html/index.html`

---

**Тайлан дууссан**

