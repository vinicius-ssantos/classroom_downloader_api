#!/usr/bin/env python3
"""
Setup script para configurar o projeto rapidamente
"""
import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def generate_encryption_key():
    """Generate and return encryption key"""
    return Fernet.generate_key().decode()


def update_env_file(key):
    """Update .env file with encryption key"""
    env_path = Path(".env")

    if not env_path.exists():
        print("❌ Arquivo .env não encontrado!")
        return False

    # Read current content
    content = env_path.read_text(encoding="utf-8")

    # Replace placeholder
    if "SUBSTITUA_PELA_CHAVE_GERADA" in content:
        content = content.replace("SUBSTITUA_PELA_CHAVE_GERADA", key)
        env_path.write_text(content, encoding="utf-8")
        print("✅ Chave de criptografia adicionada ao .env")
        return True
    elif "ENCRYPTION_KEY=" in content and key not in content:
        print("⚠️  .env já possui uma ENCRYPTION_KEY. Deseja substituir? (s/n): ", end="")
        response = input().strip().lower()
        if response == "s":
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("ENCRYPTION_KEY="):
                    lines[i] = f"ENCRYPTION_KEY={key}"
                    break
            env_path.write_text("\n".join(lines), encoding="utf-8")
            print("✅ Chave de criptografia atualizada")
            return True
    else:
        print("✅ Chave de criptografia já configurada")
        return True

    return False


def check_env_variables():
    """Check if required env variables are set"""
    print_header("Verificando Configurações")

    required_vars = {
        "GOOGLE_CLIENT_ID": "Google OAuth2 Client ID",
        "GOOGLE_CLIENT_SECRET": "Google OAuth2 Client Secret",
        "DATABASE_URL": "Database URL",
        "ENCRYPTION_KEY": "Encryption Key",
    }

    missing = []

    for var, description in required_vars.items():
        value = os.getenv(var, "")
        if not value or "your-" in value or "SUBSTITUA" in value:
            missing.append(f"  ❌ {var} - {description}")
        else:
            print(f"  ✅ {var}")

    if missing:
        print("\n⚠️  Variáveis faltando ou não configuradas:")
        for item in missing:
            print(item)
        return False

    return True


def create_downloads_dir():
    """Create downloads directory"""
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    print(f"✅ Diretório de downloads criado: {downloads_dir.absolute()}")


def main():
    """Main setup function"""
    print_header("🚀 Setup do Classroom Downloader API")

    # Step 1: Generate encryption key
    print_header("Passo 1: Gerando Chave de Criptografia")
    encryption_key = generate_encryption_key()
    print(f"Chave gerada: {encryption_key}")

    # Step 2: Update .env
    print_header("Passo 2: Atualizando .env")
    update_env_file(encryption_key)

    # Step 3: Create downloads directory
    print_header("Passo 3: Criando Diretórios")
    create_downloads_dir()

    # Step 4: Check configuration
    print_header("Passo 4: Verificando Configuração")

    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv não instalado, pulando verificação")

    # Final instructions
    print_header("📋 Próximos Passos")

    print("1. Configure as credenciais do Google OAuth2:")
    print("   - Acesse: https://console.cloud.google.com")
    print("   - Crie um projeto e habilite Classroom API + Drive API")
    print("   - Crie credenciais OAuth2")
    print("   - Adicione redirect URI: http://localhost:8001/auth/callback")
    print("   - Edite o .env e cole GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET")
    print()
    print("2. Configure o PostgreSQL:")
    print("   - Certifique-se que o PostgreSQL está rodando")
    print("   - Crie o banco: createdb classroom")
    print("   - Ou ajuste DATABASE_URL no .env")
    print()
    print("3. Rode as migrations:")
    print("   alembic upgrade head")
    print()
    print("4. Inicie a API:")
    print("   uvicorn app.main:app --reload")
    print()
    print("5. Acesse a documentação:")
    print("   http://localhost:8001/docs")
    print()
    print_header("✅ Setup Concluído!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro durante setup: {e}")
        sys.exit(1)
