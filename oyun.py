import asyncio
import re
import sys
from types import SimpleNamespace

sys.stdout.reconfigure(encoding='utf-8')

import main


class FakeCtx:
    def __init__(self, name, mentions=None):
        self.author = SimpleNamespace(name=name)
        self.message = SimpleNamespace(mentions=mentions or [])

    async def send(self, content=None, embed=None):
        if embed is not None:
            url = embed.image.url if embed.image else None
            print(f"[BOT] <görsel: {url or 'yüklenemedi'}>")
        elif content:
            lines = content.split("\n")
            print(f"[BOT] {lines[0]}")
            for line in lines[1:]:
                await asyncio.sleep(0.4 if "TUR " in line else 0.12)
                print(line)


async def give_starter(user):
    if user not in main.Pokemon.pokemons:
        try:
            await main.go.callback(FakeCtx(user))
        except Exception as e:
            print(f"Baslangic Pokemon'u verilemedi (internet baglantisini kontrol et): {e}")


async def play():
    user = "oyuncu1"
    print("=== Discord'suz Pokemon Botu ===")
    print(main.HELP_TEXT)
    print("TERMİNAL")
    print("  !user isim       Oyuncu değiştir")
    print("  q                Çıkış\n")
    await give_starter(user)
    while True:
        try:
            pokemon = main.Pokemon.pokemons.get(user)
            tag = " [SAVAŞ]" if pokemon and pokemon.battle else ""
            line = input(f"\n{user}{tag}> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line in ("q", "cik", "exit", "quit"):
            break
        if line.startswith("!user "):
            user = line.split(maxsplit=1)[1]
            print(f"Oyuncu degisti: {user}")
            await give_starter(user)
            continue
        if not line.startswith("!"):
            print("Komut ! ile baslamali.")
            continue

        parts = line[1:].split()
        cmd = main.bot.get_command(parts[0]) if parts else None
        if cmd is None:
            print(f"Bilinmeyen komut: {line}")
            continue

        mentions = [SimpleNamespace(name=m) for m in re.findall(r"@(\w+)", line)]
        args = [t for t in parts[1:] if not t.startswith("@")]
        try:
            await cmd.callback(FakeCtx(user, mentions), *args)
        except TypeError:
            print("Hatali kullanim. Ornek: !attack @veli  |  !buy potion")
        except Exception as e:
            print(f"Hata olustu (internet baglantisini kontrol et): {e}")

    print("Oyundan cikildi.")


asyncio.run(play())
