#!/usr/bin/env python3
"""
Script para importar cookies dos arquivos de requests do navegador
"""
from pathlib import Path

from app.services.cookie_manager import get_cookie_manager


def main():
    """Import cookies from curl files"""
    print("\n" + "=" * 70)
    print("🍪 IMPORTAR COOKIES DO GOOGLE")
    print("=" * 70 + "\n")

    cookie_manager = get_cookie_manager()

    # Arquivos com os requests
    classroom_file = Path("requests_classrom.txt")
    drive_file = Path("requests_drive.txt")

    all_cookies = {}

    # Parse classroom cookies
    if classroom_file.exists():
        print(f"📄 Lendo: {classroom_file}")
        classroom_cookies = cookie_manager.parse_curl_file(classroom_file)
        all_cookies.update(classroom_cookies)
        print(f"   ✅ {len(classroom_cookies)} cookies do Classroom")
    else:
        print(f"   ⚠️  Arquivo não encontrado: {classroom_file}")

    # Parse drive cookies
    if drive_file.exists():
        print(f"📄 Lendo: {drive_file}")
        drive_cookies = cookie_manager.parse_curl_file(drive_file)
        all_cookies.update(drive_cookies)
        print(f"   ✅ {len(drive_cookies)} cookies do Drive")
    else:
        print(f"   ⚠️  Arquivo não encontrado: {drive_file}")

    if not all_cookies:
        print("\n❌ Nenhum cookie encontrado!")
        print("\nVerifique se os arquivos existem:")
        print(f"  - {classroom_file.absolute()}")
        print(f"  - {drive_file.absolute()}")
        return

    # Save cookies
    print(f"\n💾 Salvando {len(all_cookies)} cookies únicos...")
    cookie_manager.save_cookies(all_cookies)

    print("\n✅ Cookies importados com sucesso!")
    print(f"📁 Salvos em: {cookie_manager.cookies_file.absolute()}")

    # Show important cookies
    important_cookies = ["SID", "HSID", "SSID", "APISID", "SAPISID"]
    print("\n🔑 Cookies importantes encontrados:")
    for cookie_name in important_cookies:
        if cookie_name in all_cookies:
            value = all_cookies[cookie_name]
            print(f"   ✅ {cookie_name}: {value[:20]}...")
        else:
            print(f"   ❌ {cookie_name}: NÃO ENCONTRADO")

    print("\n" + "=" * 70)
    print("Agora você pode usar a API sem OAuth2!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
