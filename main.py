import discord
from discord.ext import commands
from config import token
from logic import Pokemon, create_random_pokemon

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

HELP_TEXT = """=== KOMUTLAR ===
MAÇ (bot rakiplere karşı, sıra tabanlı)
  !find            Rastgele bir bot rakip bul ve özelliklerini gör
  !skip            Rakibi geç, başka rakip bul
  !fight           Bulunan rakiple savaşa başla (kazanırsan +50 altın)
  !hunt            20 altın: vahşi Pokémon ile savaş, kazanırsan yakala
SAVAŞ SIRASINDA (sen bir hamle yaparsın, sonra bot)
  !a <saldırı>     Saldır (örn: !a guclu, !a kalkan, !a delici)
  !parry           Savuştur: gelen hasarın %75'ini engelle, %30 şansla karşı saldırı
  !item <eşya>     Eşya kullan, sıranı harcar (potion, enerji, protein, vitamin, sekerleme)
  !flee            Kaç (avda %50 şans, maçta çekilirsin)
  !durum           Savaş durumunu gör
  (Olağanüstü olaylar ve %10 şansla efsanevi rakipler çıkabilir!)
SAVAŞ TAKTİKLERİ
  Gerçek Pokémon verileri: tür, güç, savunma, hız PokeAPI'den gelir
  Tür avantajı: süper etkili x2, pek etkili değil x0.5 (örn: Su > Ateş)
  Hızlı olan ilk hamleyi yapar, savunma gelen hasarı %50'ye kadar azaltır
  kalkan: hasar emer | delici: kalkanı ve savunmayı deler | parry: delici dahil her saldırıya karşı
POKÉMON
  !info            Pokémon'unun bilgileri
  !moves           Saldırı türlerini ve seviyelerini gör
  !upgrade guclu   Saldırıyı geliştir (+%15 hasar, +3 isabet / seviye, maks Sv.5)
  !feed            Ücretsiz elma ile besle (bekleme süreli)
  !feed protein    Ücretli yiyecek (enerji, protein, vitamin, sekerleme)
  !foods           Yiyecekleri ve etkilerini gör
  !attack @isim [saldırı]   Oyuncuya tek saldırı (örn: !attack @veli guclu)
EKONOMİ
  !balance         Bakiyeni gör
  !shop            Mağaza
  !buy potion      30 altın, +50 sağlık
  !buy charm       80 altın, yakalama şansı +%20
  !komutlar        Bu listeyi göster"""

@bot.event
async def on_ready():
    print(f'Giriş yapıldı: {bot.user.name}')

@bot.before_invoke
async def give_starter(ctx):
    if ctx.author.name not in Pokemon.pokemons and ctx.command.name != 'go':
        await go.callback(ctx)
        await ctx.send(HELP_TEXT)

async def send_long(ctx, text):
    for i in range(0, len(text), 1900):
        await ctx.send(text[i:i + 1900])

async def in_battle(ctx):
    pokemon = Pokemon.pokemons.get(ctx.author.name)
    if pokemon and pokemon.battle:
        await ctx.send("Savaştasın! Önce savaşı bitir.\n" + pokemon.battle.actions_text())
        return True
    return False

async def battle_of(ctx):
    pokemon = Pokemon.pokemons.get(ctx.author.name)
    if not pokemon or not pokemon.battle:
        await ctx.send("Şu an savaşta değilsin. !find ile rakip bul ya da !hunt ile ava çık.")
        return None
    return pokemon.battle

@bot.command()
async def go(ctx):
    author = ctx.author.name
    if author not in Pokemon.pokemons:
        pokemon = create_random_pokemon(author)
        await ctx.send(f"Hoş geldin! Başlangıç hediyesi olarak rastgele bir {type(pokemon).__name__} Pokémon kazandın!")
        await ctx.send(await pokemon.info())
        image_url = await pokemon.show_img()
        if image_url:
            embed = discord.Embed()
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Pokemon görüntüsü yüklenemedi.")
    else:
        await ctx.send("Zaten bir Pokemon oluşturdunuz.")

@bot.command()
async def attack(ctx, *args):
    if await in_battle(ctx):
        return
    target = ctx.message.mentions[0] if ctx.message.mentions else None
    move = next((a.lower() for a in args if not a.startswith(("<@", "@"))), None)
    if target and target.name == ctx.author.name:
        await ctx.send("Kendi Pokémon'una saldıramazsın!")
    elif target:
        if target.name in Pokemon.pokemons and ctx.author.name in Pokemon.pokemons:
            enemy = Pokemon.pokemons[target.name]
            attacker = Pokemon.pokemons[ctx.author.name]
            result = await attacker.attack(enemy, move)
            await ctx.send(result)
        else:
            await ctx.send("Savaşmak için her iki katılımcının da Pokemon sahibi olması gerekir!")
    else:
        await ctx.send("Saldırmak istediğiniz kullanıcıyı etiketleyerek belirtin.")

@bot.command()
async def info(ctx):
    author = ctx.author.name
    if author in Pokemon.pokemons:
        pokemon = Pokemon.pokemons[author]
        await ctx.send(await pokemon.info())
    else:
        await ctx.send("Pokémon sahibi değilsiniz!")

@bot.command()
async def feed(ctx, food=None):
    if await in_battle(ctx):
        return
    author = ctx.author.name
    if author in Pokemon.pokemons:
        pokemon = Pokemon.pokemons[author]
        await ctx.send(await pokemon.feed(food.lower() if food else None))
    else:
        await ctx.send("Pokémon sahibi değilsiniz!")

@bot.command()
async def balance(ctx):
    author = ctx.author.name
    if author in Pokemon.pokemons:
        pokemon = Pokemon.pokemons[author]
        await ctx.send(f"Bakiyen: {pokemon.money} altın")
    else:
        await ctx.send("Pokémon sahibi değilsiniz!")

@bot.command()
async def shop(ctx):
    author = ctx.author.name
    if author in Pokemon.pokemons:
        pokemon = Pokemon.pokemons[author]
        await ctx.send(pokemon.shop())
    else:
        await ctx.send("Pokémon sahibi değilsiniz!")

@bot.command()
async def buy(ctx, item=None):
    if await in_battle(ctx):
        return
    author = ctx.author.name
    if author not in Pokemon.pokemons:
        await ctx.send("Pokémon sahibi değilsiniz!")
        return
    if not item:
        await ctx.send("Ne almak istediğini yaz: !buy potion veya !buy charm")
        return
    pokemon = Pokemon.pokemons[author]
    await ctx.send(pokemon.buy(item.lower()))

@bot.command()
async def hunt(ctx):
    if await in_battle(ctx):
        return
    await send_long(ctx, await Pokemon.pokemons[ctx.author.name].hunt())

@bot.command()
async def find(ctx):
    if await in_battle(ctx):
        return
    await send_long(ctx, await Pokemon.pokemons[ctx.author.name].find_opponent())

@bot.command()
async def skip(ctx):
    if await in_battle(ctx):
        return
    await send_long(ctx, await Pokemon.pokemons[ctx.author.name].skip_opponent())

@bot.command()
async def fight(ctx):
    if await in_battle(ctx):
        return
    await send_long(ctx, await Pokemon.pokemons[ctx.author.name].fight())

@bot.command(name='a', aliases=['saldir'])
async def battle_attack(ctx, move=None):
    battle = await battle_of(ctx)
    if not battle:
        return
    if not move:
        await ctx.send("Hangi saldırı? Örn: !a guclu\n" + battle.player.moves_text())
        return
    await send_long(ctx, await battle.player_turn('attack', move.lower()))

@bot.command()
async def parry(ctx):
    battle = await battle_of(ctx)
    if battle:
        await send_long(ctx, await battle.player_turn('parry'))

@bot.command()
async def item(ctx, name=None):
    battle = await battle_of(ctx)
    if not battle:
        return
    if not name:
        await ctx.send(f"Hangi eşya? Örn: !item enerji\n{battle.player.foods_text()}\n"
                       f"  potion     30 altın - Pokémon sağlığına +50 ekler")
        return
    await send_long(ctx, await battle.player_turn('item', name.lower()))

@bot.command(aliases=['kac'])
async def flee(ctx):
    battle = await battle_of(ctx)
    if battle:
        await send_long(ctx, await battle.player_turn('flee'))

@bot.command()
async def durum(ctx):
    battle = await battle_of(ctx)
    if battle:
        await send_long(ctx, battle.player.moves_text() + "\n" + battle.status())

@bot.command()
async def moves(ctx):
    await ctx.send(Pokemon.pokemons[ctx.author.name].moves_text())

@bot.command()
async def upgrade(ctx, move=None):
    if await in_battle(ctx):
        return
    pokemon = Pokemon.pokemons[ctx.author.name]
    if not move:
        await ctx.send("Hangi saldırıyı geliştireceğini yaz, örn: !upgrade guclu\n" + pokemon.moves_text())
        return
    await ctx.send(pokemon.upgrade(move.lower()))

@bot.command()
async def foods(ctx):
    await ctx.send(Pokemon.pokemons[ctx.author.name].foods_text())

@bot.command()
async def komutlar(ctx):
    await ctx.send(HELP_TEXT)

if __name__ == "__main__":
    bot.run(token)
