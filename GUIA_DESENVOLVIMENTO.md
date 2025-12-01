# 🛠️ Guia de Desenvolvimento

Este guia mostra como usar as ferramentas de qualidade e testes configuradas no projeto.

---

## 📦 Setup Inicial

```bash
# 1. Ativar ambiente virtual
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# 3. Instalar pre-commit hooks
pre-commit install

# Pronto! Agora os hooks rodam automaticamente em cada commit
```

---

## 🧪 Rodando Testes

### Todos os testes

```bash
pytest
```

### Com coverage report

```bash
pytest --cov=app --cov-report=term-missing
```

Saída esperada:
```
tests/integration/test_health_router.py ✓✓✓
tests/integration/test_courses_router.py ✓✓✓✓✓
tests/integration/test_downloads_router.py ✓✓✓✓✓✓
tests/unit/test_repositories.py ✓✓✓✓✓✓✓✓

---------- coverage: platform linux, python 3.11.x -----------
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
app/__init__.py                       0      0   100%
app/main.py                          45     12    73%   56-62
app/api/routers/health.py            12      2    83%   23-24
...
---------------------------------------------------------------
TOTAL                               450    135    70%
```

### Apenas testes rápidos (unit)

```bash
pytest -m unit
```

### Apenas testes de integração

```bash
pytest -m integration
```

### Rodando um arquivo específico

```bash
pytest tests/integration/test_health_router.py
```

### Rodando um teste específico

```bash
pytest tests/integration/test_health_router.py::test_health_endpoint_returns_ok
```

### Com mais verbosidade

```bash
pytest -v  # verbose
pytest -vv  # very verbose
pytest -s  # show print statements
```

### Testes em paralelo (mais rápido)

```bash
pytest -n auto  # usa todos os CPUs
pytest -n 4  # usa 4 workers
```

---

## 🎨 Code Formatting e Linting

### Black (formatação automática)

```bash
# Verificar o que seria formatado
black --check app/ tests/

# Aplicar formatação
black app/ tests/
```

### Ruff (linting)

```bash
# Verificar problemas
ruff check app/ tests/

# Auto-fix problemas quando possível
ruff check --fix app/ tests/
```

### isort (organizar imports)

```bash
# Verificar
isort --check-only --profile black app/ tests/

# Aplicar
isort --profile black app/ tests/
```

### MyPy (type checking)

```bash
mypy app/
```

---

## 🔒 Security Checks

### Bandit (security linting)

```bash
# Scan completo
bandit -r app/

# Apenas problemas de alta severidade
bandit -r app/ -ll
```

### Safety (vulnerabilidades em dependências)

```bash
safety check
```

---

## 🪝 Pre-commit Hooks

### Rodar hooks manualmente

```bash
# Em todos os arquivos
pre-commit run --all-files

# Apenas nos arquivos staged
pre-commit run
```

### Atualizar hooks

```bash
pre-commit autoupdate
```

### Pular hooks temporariamente (emergências)

```bash
git commit --no-verify -m "emergency fix"
```

**⚠️ Evite pular hooks! Use apenas em emergências.**

---

## 🚀 Workflow de Desenvolvimento Recomendado

### 1. Antes de começar a codar

```bash
# Atualizar branch
git pull origin main

# Criar branch de feature
git checkout -b feature/minha-feature

# Rodar testes para garantir que está tudo ok
pytest
```

### 2. Durante o desenvolvimento

```bash
# Escrever código
# ...

# Rodar testes relevantes frequentemente
pytest tests/unit/test_meu_modulo.py -v

# Verificar formatação
black app/services/meu_service.py
```

### 3. Antes do commit

```bash
# Rodar todos os testes
pytest

# Verificar coverage
pytest --cov=app --cov-report=term-missing

# (Opcional) Rodar pre-commit manualmente
pre-commit run --all-files

# Se tudo passou, commit
git add .
git commit -m "feat: adicionar funcionalidade X"
# Pre-commit hooks rodam automaticamente!
```

### 4. Antes do push

```bash
# Rodar testes finais
pytest --cov=app

# Push
git push origin feature/minha-feature
```

### 5. Criar Pull Request

O CI rodará automaticamente:
- ✅ Code quality (Black, Ruff, isort, MyPy)
- ✅ Tests (Python 3.11 e 3.12)
- ✅ Security scan (Bandit, Safety)
- ✅ Docker build

---

## 📊 Coverage Reports

### Gerar report HTML

```bash
pytest --cov=app --cov-report=html
```

Abrir `htmlcov/index.html` no navegador para visualização interativa.

### Gerar report XML (para CI)

```bash
pytest --cov=app --cov-report=xml
```

Arquivo `coverage.xml` será criado.

---

## 🐛 Debugging de Testes

### Parar no primeiro erro

```bash
pytest -x
```

### Mostrar output de print statements

```bash
pytest -s
```

### Entrar no debugger ao falhar

```bash
pytest --pdb
```

### Ver quais testes seriam executados

```bash
pytest --collect-only
```

---

## 🔧 Configurações Personalizadas

### Modificar threshold de coverage

Editar `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = [
    "--cov-fail-under=80",  # Mudar de 70% para 80%
]
```

### Adicionar mais regras de linting

Editar `pyproject.toml`:
```toml
[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "C", "B", "UP", "N", "S", "RUF",
    "ANN",  # adicionar type annotations check
]
```

### Ignorar arquivos no pre-commit

Editar `.pre-commit-config.yaml`:
```yaml
- id: black
  exclude: ^migrations/|^scripts/
```

---

## 📝 Escrevendo Novos Testes

### Template de teste de integração

```python
# tests/integration/test_meu_router.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_meu_endpoint(client: AsyncClient):
    """Descrição do que o teste faz"""
    response = await client.get("/meu-endpoint")

    assert response.status_code == 200
    data = response.json()
    assert "campo" in data
```

### Template de teste unitário

```python
# tests/unit/test_meu_service.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.meu_service import MeuService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_meu_service_funcao(db_session: AsyncSession):
    """Descrição do que o teste faz"""
    service = MeuService(db_session)

    result = await service.minha_funcao(parametro=123)

    assert result is not None
    assert result.campo == "esperado"
```

### Usando fixtures customizadas

```python
# tests/conftest.py (adicionar)
@pytest.fixture
def meu_mock_data():
    return {"campo": "valor"}

# tests/unit/test_algo.py (usar)
def test_com_fixture(meu_mock_data):
    assert meu_mock_data["campo"] == "valor"
```

---

## 🆘 Troubleshooting

### Erro: "Module not found"

```bash
# Reinstalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Erro: "Database locked" (SQLite em tests)

```bash
# Rodar testes sequencialmente
pytest -n 0
```

### Pre-commit muito lento

```bash
# Desabilitar hooks pesados temporariamente
SKIP=mypy git commit -m "mensagem"
```

### Coverage muito baixo

```bash
# Ver o que não está coberto
pytest --cov=app --cov-report=term-missing

# Focar nos arquivos com baixa cobertura
pytest --cov=app/services/meu_service.py
```

---

## 📚 Recursos Adicionais

- **Pytest docs:** https://docs.pytest.org/
- **Black docs:** https://black.readthedocs.io/
- **Ruff docs:** https://docs.astral.sh/ruff/
- **MyPy docs:** https://mypy.readthedocs.io/
- **Pre-commit docs:** https://pre-commit.com/

---

## ✅ Checklist de Qualidade

Antes de mergear sua branch, certifique-se que:

- [ ] Todos os testes passam: `pytest`
- [ ] Coverage >= 70%: `pytest --cov=app`
- [ ] Black passou: `black --check app/ tests/`
- [ ] Ruff passou: `ruff check app/ tests/`
- [ ] MyPy passou: `mypy app/`
- [ ] Pre-commit hooks passam: `pre-commit run --all-files`
- [ ] CI verde no GitHub Actions
- [ ] Código revisado por pelo menos 1 pessoa

---

**Bom desenvolvimento! 🚀**
