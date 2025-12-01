#!/usr/bin/env python3
"""
Script to generate Fernet encryption key for storing Google OAuth2 credentials
"""
from cryptography.fernet import Fernet


def main():
    """Generate and print a new Fernet encryption key"""
    key = Fernet.generate_key()
    print("\n" + "=" * 70)
    print("🔐 ENCRYPTION KEY GERADA COM SUCESSO!")
    print("=" * 70)
    print("\nCopie a chave abaixo e cole no seu arquivo .env:")
    print(f"\nENCRYPTION_KEY={key.decode()}")
    print("\n" + "=" * 70)
    print("\nIMPORTANTE:")
    print("  - Mantenha esta chave segura e NUNCA commite no git")
    print("  - Use a mesma chave em todos os ambientes")
    print("  - Se perder a chave, todos os usuários precisarão autenticar novamente")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
