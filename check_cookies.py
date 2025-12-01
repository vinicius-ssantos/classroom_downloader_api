#!/usr/bin/env python3
"""
Script para verificar se você tem todos os cookies necessários
"""
from pathlib import Path

from app.services.cookie_manager import get_cookie_manager


def main():
    """Check if all required cookies are present"""
    print("\n" + "=" * 70)
    print("🔍 VERIFICAR COOKIES")
    print("=" * 70 + "\n")

    cookie_manager = get_cookie_manager()

    # Check if cookies file exists
    if not cookie_manager.has_cookies():
        print("❌ Cookies não encontrados!")
        print(f"📁 Esperado em: {cookie_manager.cookies_file.absolute()}")
        print("\n💡 Execute primeiro: python import_cookies.py")
        return

    # Load cookies
    cookies = cookie_manager.load_cookies()

    if not cookies:
        print("❌ Erro ao carregar cookies!")
        return

    print(f"✅ Cookies carregados: {len(cookies)} cookies\n")

    # Essential cookies
    essential_cookies = {
        "SID": "Session ID - Identifica sua sessão Google",
        "HSID": "Host Session ID - Sessão específica do host",
        "SSID": "Secure Session ID - Versão segura da sessão",
        "APISID": "API Session ID - Acesso às APIs",
        "SAPISID": "Secure API Session ID - Acesso seguro às APIs",
    }

    # Recommended cookies
    recommended_cookies = {
        "__Secure-1PSID": "Secure Session ID (primary)",
        "__Secure-3PSID": "Secure Session ID (cross-site)",
        "__Secure-1PAPISID": "Secure API ID (primary)",
        "__Secure-3PAPISID": "Secure API ID (cross-site)",
    }

    # Optional cookies
    optional_cookies = {
        "__Secure-1PSIDTS": "Session timestamp",
        "__Secure-3PSIDTS": "Session timestamp (cross-site)",
        "SIDCC": "Session cookie consent",
    }

    # Check essential
    print("🔑 COOKIES ESSENCIAIS:")
    missing_essential = []
    for cookie_name, description in essential_cookies.items():
        if cookie_name in cookies:
            value = cookies[cookie_name]
            print(f"   ✅ {cookie_name:15} - {description}")
            print(f"      Valor: {value[:50]}...")
        else:
            print(f"   ❌ {cookie_name:15} - {description} - NÃO ENCONTRADO")
            missing_essential.append(cookie_name)

    # Check recommended
    print("\n📋 COOKIES RECOMENDADOS:")
    missing_recommended = []
    for cookie_name, description in recommended_cookies.items():
        if cookie_name in cookies:
            print(f"   ✅ {cookie_name:20} - {description}")
        else:
            print(f"   ⚠️  {cookie_name:20} - {description} - Não encontrado")
            missing_recommended.append(cookie_name)

    # Check optional
    print("\n🔧 COOKIES OPCIONAIS:")
    for cookie_name, description in optional_cookies.items():
        if cookie_name in cookies:
            print(f"   ✅ {cookie_name:20} - {description}")
        else:
            print(f"   ⚪ {cookie_name:20} - {description} - Não encontrado")

    # Summary
    print("\n" + "=" * 70)
    if missing_essential:
        print("❌ ATENÇÃO: Cookies essenciais faltando!")
        print(f"   Faltando: {', '.join(missing_essential)}")
        print("\n💡 Solução:")
        print("   1. Acesse Google Classroom no navegador")
        print("   2. Faça login")
        print("   3. F12 → Network → Copie um request como cURL")
        print("   4. Cole em requests_classrom.txt")
        print("   5. Execute: python import_cookies.py")
    elif missing_recommended:
        print("⚠️  Cookies essenciais OK, mas alguns recomendados estão faltando")
        print(f"   Faltando: {', '.join(missing_recommended)}")
        print("\n💡 A API deve funcionar, mas pode ter problemas em alguns casos")
    else:
        print("✅ TODOS OS COOKIES IMPORTANTES ENCONTRADOS!")
        print("\n🎉 Sua autenticação está configurada corretamente!")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
