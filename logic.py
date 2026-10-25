import aiohttp
import asyncio
import random
from random import randint
from datetime import datetime, timedelta

class Pokemon:
    pokemons = {}

    def __init__(self, pokemon_trainer, register=True):
        self.pokemon_trainer = pokemon_trainer
        self.pokemon_number = random.randint(1, 1000)
        self.name = None
        self.img = None
        self.power = random.randint(30, 60)
        self.hp = random.randint(200, 400)
        self.max_hp = self.hp
        self.last_feed_time = datetime.now()
        self.money = 50
        self.charm = False
        self.opponent = None
        self.move_levels = {}
        self.types = ['normal']
        self.defense = 50
        self.speed = 50
        self.shield = 0
        self.parrying = False
        self.battle = None
        self.loaded = False
        if register and pokemon_trainer not in self.pokemons:
            self.pokemons[pokemon_trainer] = self

    TYPE_TR = {'normal': 'Normal', 'fire': 'Ateş', 'water': 'Su', 'grass': 'Çimen',
               'electric': 'Elektrik', 'ice': 'Buz', 'fighting': 'Dövüş', 'poison': 'Zehir',
               'ground': 'Toprak', 'flying': 'Uçan', 'psychic': 'Psişik', 'bug': 'Böcek',
               'rock': 'Kaya', 'ghost': 'Hayalet', 'dragon': 'Ejderha', 'dark': 'Karanlık',
               'steel': 'Çelik', 'fairy': 'Peri'}
    type_cache = {}

    @staticmethod
    async def fetch_json(url):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    return await response.json() if response.status == 200 else None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    async def load(self):
        if self.loaded:
            return
        self.loaded = True
        data = await self.fetch_json(f'https://pokeapi.co/api/v2/pokemon/{self.pokemon_number}')
        if not data:
            self.name = self.name or "pikachu"
            return
        stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
        self.name = data['name']
        self.img = data['sprites']['front_default']
        self.types = [t['type']['name'] for t in data['types']]
        self.hp = self.max_hp = 150 + stats['hp'] * 2
        self.power = 15 + max(stats['attack'], stats['special-attack']) // 3
        self.defense = (stats['defense'] + stats['special-defense']) // 2
        self.speed = stats['speed']

    def type_text(self):
        return "/".join(self.TYPE_TR.get(t, t) for t in self.types)

    async def type_multiplier(self, attack_type, defender):
        rel = Pokemon.type_cache.get(attack_type)
        if rel is None:
            data = await self.fetch_json(f'https://pokeapi.co/api/v2/type/{attack_type}')
            if not data:
                return 1.0
            dr = data['damage_relations']
            rel = {key: {t['name'] for t in dr[f'{key}_damage_to']} for key in ('double', 'half', 'no')}
            Pokemon.type_cache[attack_type] = rel
        mult = 1.0
        for t in defender.types:
            if t in rel['double']:
                mult *= 2
            elif t in rel['half']:
                mult *= 0.5
            elif t in rel['no']:
                mult *= 0
        return mult

    async def get_name(self):
        await self.load()
        return self.name

    async def info(self):
        await self.load()
        return (f"Pokémon ismi: {self.name} ({type(self).__name__})\n"
                f"Tür: {self.type_text()}\n"
                f"Güç: {self.power} | Savunma: {self.defense} | Hız: {self.speed}\n"
                f"Sağlık: {self.hp}/{self.max_hp}")

    async def show_img(self):
        await self.load()
        return self.img

    MOVES = {
        'normal': {'name': 'Normal Saldırı', 'mult': 1.0, 'acc': 100, 'hits': 1},
        'guclu': {'name': 'Güçlü Vuruş', 'mult': 1.6, 'acc': 70, 'hits': 1},
        'hizli': {'name': 'Hızlı Saldırı', 'mult': 0.6, 'acc': 95, 'hits': 2},
        'iyiles': {'name': 'İyileşme', 'heal': 40},
        'kalkan': {'name': 'Kalkan', 'shield': 50},
        'delici': {'name': 'Delici Saldırı', 'mult': 0.9, 'acc': 85, 'hits': 1, 'pierce': True},
    }
    CRIT_CHANCE = 10
    MAX_SHIELD = 200

    FLAVOR = {
        'normal': ["{a} hızla koşup {d} üzerine sert bir darbe indirdi!",
                   "{a} dişlerini gösterip {d} üzerine atıldı!"],
        'guclu': ["{a} tüm gücünü topladı... yer sarsılıyor!",
                  "{a} havaya sıçradı ve ağır bir darbe için yüklendi!"],
        'hizli': ["{a} gözle görülemeyecek bir hızla iki kez vurdu!",
                  "{a} şimşek gibi {d} etrafında dönüp saldırdı!"],
        'iyiles': ["{a} gözlerini kapadı, yeşil bir ışık onu sardı...",
                   "{a} derin bir nefes aldı ve yaralarını sardı."],
        'atestopu': ["{a} ellerinde dev bir ateş topu büyütüyor... ve FIRLATTI!",
                     "Arena alevlere boğuldu! {a} ateş topunu savurdu!"],
        'buz': ["{a} havada üç buz oku oluşturdu ve {d} üzerine yolladı!",
                "Hava birden soğudu... {a} buz oklarını saldı!"],
        'kombo': ["{a} yumruk yağmuruna başladı: sol, sağ, sol, sağ!",
                  "{a}, {d} üzerine dört vuruşluk bir kombo patlattı!"],
        'tekme': ["{a} havaya fırladı ve uçan tekmesini savurdu!",
                  "{a} arenanın öbür ucundan koşup uçan tekme attı!"],
        'kalkan': ["{a} önünde parlayan bir enerji kalkanı yükseltti!",
                   "{a} savunmaya geçti, etrafını sert bir kalkan sardı!"],
        'delici': ["{a} enerjisini tek bir noktaya topladı ve delici bir darbe savurdu!",
                   "{a} kalkanları hiçe sayarak mızrak gibi saldırdı!"],
    }
    MISS_TEXT = ["Ama {d} son anda yana kaçtı! ISKA!",
                 "Kıl payı! Saldırı boşa gitti, seyirciler hayal kırıklığında!"]

    def label(self):
        return f"{self.name or 'Pokémon'} (@{self.pokemon_trainer})"

    def hp_bar(self, width=20):
        self.max_hp = max(self.max_hp, self.hp, 1)
        filled = round(width * self.hp / self.max_hp)
        shield = f" | Kalkan: {self.shield}" if self.shield > 0 else ""
        return f"{self.label()}: [{'█' * filled}{'░' * (width - filled)}] {self.hp}/{self.max_hp} HP{shield}"

    def power_bonus(self):
        return 0, ""

    def choose_move(self):
        options = list(self.MOVES)
        if self.shield > 0:
            options.remove('kalkan')
        if self.hp >= self.max_hp:
            options.remove('iyiles')
        return random.choice(options)

    MAX_MOVE_LEVEL = 5

    def move_stats(self, move):
        m = dict(self.MOVES[move])
        lvl = self.move_levels.get(move, 0)
        if 'heal' in m:
            m['heal'] += 15 * lvl
        elif 'shield' in m:
            m['shield'] += 15 * lvl + self.defense // 2
        else:
            m['type'] = m.get('type') or self.types[0]
            m['mult'] = round(m['mult'] * (1 + 0.15 * lvl), 2)
            m['acc'] = min(100, m['acc'] + 3 * lvl)
        m['level'] = lvl
        return m

    def upgrade_cost(self, move):
        return 40 * (self.move_levels.get(move, 0) + 1)

    def moves_text(self):
        lines = []
        for key in self.MOVES:
            m = self.move_stats(key)
            lvl = f"Sv.{m['level']}"
            cost = ("MAKS" if m['level'] >= self.MAX_MOVE_LEVEL
                    else f"geliştir: {self.upgrade_cost(key)} altın")
            if 'heal' in m:
                lines.append(f"  {key:<9} {m['name']} [{lvl}]: +{m['heal']} sağlık ({cost})")
            elif 'shield' in m:
                lines.append(f"  {key:<9} {m['name']} [{lvl}]: {m['shield']} hasar emen kalkan ({cost})")
            else:
                pierce = ", kalkan ve savunmayı deler" if m.get('pierce') else ""
                lines.append(f"  {key:<9} {m['name']} [{lvl}]: {self.TYPE_TR.get(m['type'], m['type'])} türü, "
                             f"{m['hits']}x vuruş, güç x{m['mult']}, isabet %{m['acc']}{pierce} ({cost})")
        return (f"{type(self).__name__} ({self.type_text()}) saldırıları:\n" + "\n".join(lines) +
                f"\nGeliştirmek için: !upgrade <saldırı>  (her seviye: +%15 hasar, +3 isabet / +15 iyileşme / +15 kalkan)"
                f"\nBakiye: {self.money} altın")

    def upgrade(self, move):
        if move not in self.MOVES:
            return f"Bilinmeyen saldırı: {move}\n{self.moves_text()}"
        lvl = self.move_levels.get(move, 0)
        if lvl >= self.MAX_MOVE_LEVEL:
            return f"{self.MOVES[move]['name']} zaten maksimum seviyede (Sv.{lvl})!"
        cost = self.upgrade_cost(move)
        if self.money < cost:
            return f"Yetersiz bakiye! Gereken: {cost}, sende: {self.money}"
        self.money -= cost
        self.move_levels[move] = lvl + 1
        m = self.move_stats(move)
        effect = (f"iyileşme +{m['heal']}" if 'heal' in m
                  else f"kalkan {m['shield']}" if 'shield' in m
                  else f"güç x{m['mult']}, isabet %{m['acc']}")
        return (f"{m['name']} geliştirildi! Sv.{lvl} -> Sv.{lvl + 1} ({effect})\n"
                f"Kalan bakiye: {self.money} altın")

    async def attack(self, enemy, move=None):
        if self.hp <= 0:
            return "Pokémon'un yenik durumda! Önce !feed veya !buy potion ile iyileştir."
        if enemy.hp <= 0:
            return f"@{enemy.pokemon_trainer}'nin Pokémon'u zaten yenildi!"
        if move is None:
            move = self.choose_move()
        if move not in self.MOVES:
            return f"Bilinmeyen saldırı: {move}\n{self.moves_text()}"
        m = self.move_stats(move)
        a, d = self.label(), enemy.label()
        lvl = f" Sv.{m['level']}" if m['level'] else ""
        lines = [f">> {a} [{m['name'].replace('i', 'İ').upper()}{lvl}] kullanıyor!"]
        if move in self.FLAVOR:
            lines.append("   " + random.choice(self.FLAVOR[move]).format(a=a, d=d))

        if 'heal' in m:
            self.hp += m['heal']
            lines.append(f"   +{m['heal']} sağlık kazandı!")
            lines.append("   " + self.hp_bar())
            return "\n".join(lines)
        if 'shield' in m:
            self.shield = min(self.MAX_SHIELD, max(self.shield, m['shield']))
            lines.append(f"   {self.shield} hasar emebilen bir kalkan oluştu!")
            lines.append("   " + self.hp_bar())
            return "\n".join(lines)
        pierce = m.get('pierce', False)
        if not pierce and isinstance(enemy, Wizard) and randint(1, 5) == 1:
            lines.append(f"   {d} sihirli bir kalkan açtı! Saldırı kalkana çarpıp dağıldı!")
            return "\n".join(lines)
        if randint(1, 100) > m['acc']:
            lines.append("   " + random.choice(self.MISS_TEXT).format(d=d))
            return "\n".join(lines)

        bonus, bonus_text = self.power_bonus()
        damage = sum(int((self.power + bonus) * m['mult']) for _ in range(m['hits']))
        if bonus_text:
            lines.append(f"   {bonus_text}")

        effect = await self.type_multiplier(m['type'], enemy)
        type_name = self.TYPE_TR.get(m['type'], m['type'])
        if effect >= 2:
            lines.append(f"   {type_name} saldırısı {enemy.type_text()} türüne karşı SÜPER ETKİLİ! (x{effect:g})")
        elif effect == 0:
            lines.append(f"   {enemy.type_text()} türü {type_name} saldırılarına karşı bağışık... neredeyse hiç etkisi yok! (x0.25)")
        elif effect < 1:
            lines.append(f"   {type_name} saldırısı {enemy.type_text()} türüne karşı pek etkili değil... (x{effect:g})")
        damage *= max(effect, 0.25)

        if randint(1, 100) <= self.CRIT_CHANCE:
            damage *= 2
            lines.append("   KRİTİK VURUŞ!!! Seyirciler ayakta! Hasar 2 katına çıktı!")
        if not pierce:
            damage *= 1 - min(0.5, enemy.defense / 400)
        damage = max(1, int(damage))

        if enemy.parrying:
            if randint(1, 100) <= 30:
                counter = max(1, damage // 2)
                self.hp = max(0, self.hp - counter)
                lines.append(f"   MÜKEMMEL PARRY! {d} saldırıyı tam zamanında savuşturdu "
                             f"ve karşı saldırıyla {counter} hasar verdi!")
                lines.append("   " + self.hp_bar())
                damage = 0
            else:
                damage = max(1, damage // 4)
                lines.append(f"   {d} PARRY yaptı! Hasarın %75'i savuşturuldu!")

        if damage and enemy.shield > 0 and pierce:
            lines.append(f"   Delici saldırı {d} kalkanını delip geçti!")
        elif damage and enemy.shield > 0:
            absorbed = min(enemy.shield, damage)
            enemy.shield -= absorbed
            damage -= absorbed
            lines.append(f"   {d} kalkanı {absorbed} hasarı emdi!"
                         + (" KALKAN PARAMPARÇA OLDU!" if enemy.shield == 0 else f" (Kalan kalkan: {enemy.shield})"))
        enemy.hp = max(0, enemy.hp - damage)
        hits = f" ({m['hits']} vuruş)" if m['hits'] > 1 else ""
        lines.append(f"   {d} {damage} hasar aldı{hits}!" if damage else f"   {d} hiç hasar almadı!")
        lines.append("   " + enemy.hp_bar())

        if enemy.hp > 0:
            if enemy.hp <= max(enemy.max_hp, 1) * 0.25:
                lines.append(f"   {d} sendeliyor... zor durumda!")
            return "\n".join(lines)
        lines.append(f"   *** {d} YERE YIĞILDI! NAKAVT! ***")
        lines.append(f"   Pokémon eğitmeni @{self.pokemon_trainer}, @{enemy.pokemon_trainer} karşısında kazandı!")
        if Pokemon.pokemons.get(self.pokemon_trainer) is self and self.battle is None:
            self.money += 50
            lines.append(f"   +50 altın kazandın! Bakiye: {self.money}")
        return "\n".join(lines)

    FOODS = {
        'elma': {'price': 0, 'desc': 'Ücretsiz, bekleme süreli temel besleme'},
        'enerji': {'price': 20, 'desc': 'Anında +60 sağlık (bekleme yok)'},
        'protein': {'price': 35, 'desc': 'Kalıcı +5 güç'},
        'vitamin': {'price': 45, 'desc': 'Maksimum sağlık +40 ve tam iyileşme'},
        'sekerleme': {'price': 60, 'desc': 'Kritik vuruş şansı kalıcı +%3 (en fazla %25)'},
    }

    def foods_text(self):
        return "YİYECEKLER (!feed <yiyecek>)\n" + "\n".join(
            f"  {name:<10} {'ücretsiz' if f['price'] == 0 else str(f['price']) + ' altın'} - {f['desc']}"
            for name, f in self.FOODS.items())

    async def feed(self, food=None, feed_interval=60, hp_increase=10):
        food = food or 'elma'
        if food not in self.FOODS:
            return f"Böyle bir yiyecek yok: {food}\n{self.foods_text()}"
        if food == 'elma':
            current_time = datetime.now()
            delta_time = timedelta(seconds=feed_interval)
            if (current_time - self.last_feed_time) > delta_time:
                self.hp += hp_increase
                self.last_feed_time = current_time
                return f"Pokémon'un sağlığı geri yüklenir. Mevcut sağlık: {self.hp}"
            else:
                return (f"Pokémon'unuzu şu zaman besleyebilirsiniz: {self.last_feed_time + delta_time}\n"
                        f"Beklemek istemiyorsan ücretli yiyecek dene:\n{self.foods_text()}")

        price = self.FOODS[food]['price']
        if food == 'sekerleme' and self.CRIT_CHANCE >= 25:
            return "Kritik şansın zaten maksimumda (%25)!"
        if self.money < price:
            return f"Yetersiz bakiye! Gereken: {price}, sende: {self.money}"
        self.money -= price
        if food == 'enerji':
            self.hp += 60
            result = f"Enerji içeceği içildi! +60 sağlık"
        elif food == 'protein':
            self.power += 5
            result = f"Protein yendi! Güç kalıcı olarak +5 -> {self.power}"
        elif food == 'vitamin':
            self.max_hp = max(self.max_hp, self.hp) + 40
            self.hp = self.max_hp
            result = f"Vitamin alındı! Maksimum sağlık +40 ve tam iyileşme"
        else:
            self.CRIT_CHANCE = min(25, self.CRIT_CHANCE + 3)
            result = f"Şekerleme yendi! Kritik vuruş şansı -> %{self.CRIT_CHANCE}"
        return f"{result}\n{self.hp_bar()}\nKalan bakiye: {self.money} altın"

    SHOP = {
        'potion': {'price': 30, 'desc': 'Pokémon sağlığına +50 ekler'},
        'charm': {'price': 80, 'desc': 'Avda yakalama şansını +%20 artırır (kalıcı)'},
    }

    def shop(self):
        items = "\n".join(f"  {name:<10} {data['price']} altın - {data['desc']}"
                          for name, data in self.SHOP.items())
        return (f"MAĞAZA (!buy <eşya>)\n{items}\n{self.foods_text()}\n"
                f"SALDIRI GELİŞTİRME: !moves ile seviyeleri gör, !upgrade <saldırı> ile geliştir\n"
                f"Bakiyen: {self.money} altın")

    BATTLE_ITEMS = ['potion', 'enerji', 'protein', 'vitamin', 'sekerleme']

    async def use_item(self, item):
        if item not in self.BATTLE_ITEMS:
            return False, f"Savaşta kullanılabilecek eşyalar: {', '.join(self.BATTLE_ITEMS)}"
        before = self.money
        text = self.buy(item) if item == 'potion' else await self.feed(item)
        return self.money < before, text

    def buy(self, item):
        if item not in self.SHOP:
            return f"Böyle bir eşya yok. Mağazayı görmek için !shop yaz."
        if item == 'charm' and self.charm:
            return "Zaten şans tılsımın var!"
        price = self.SHOP[item]['price']
        if self.money < price:
            return f"Yetersiz bakiye! Gereken: {price}, sende: {self.money}"
        self.money -= price
        if item == 'potion':
            self.hp += 50
            return f"İksir kullanıldı! Yeni sağlık: {self.hp}. Kalan bakiye: {self.money}"
        self.charm = True
        return f"Şans tılsımı alındı! Av şansın artık +%20. Kalan bakiye: {self.money}"

    def stats(self):
        return (f"{self.name} ({type(self).__name__}) | Tür: {self.type_text()} | Eğitmen: {self.pokemon_trainer}\n"
                f"       Güç: {self.power} | Savunma: {self.defense} | Hız: {self.speed} | Sağlık: {self.hp}/{self.max_hp}")

    async def random_event(self, enemy):
        event = randint(1, 6)
        lucky, unlucky = random.sample([self, enemy], 2)
        head = "!!! OLAĞANÜSTÜ OLAY !!!\n   "
        if event == 1:
            self.hp, enemy.hp = max(1, self.hp - 25), max(1, enemy.hp - 25)
            return (head + "Gökyüzü karardı... GÜM! Arenanın ortasına şimşek düştü!\n"
                    "   İki Pokémon da 25 hasar aldı!\n   " + self.hp_bar() + "\n   " + enemy.hp_bar())
        if event == 2:
            lucky.hp += 40
            return (head + f"{lucky.label()} yerde parlayan şifalı bir bitki buldu ve yedi!\n"
                    f"   +40 sağlık!\n   " + lucky.hp_bar())
        if event == 3:
            return (head + f"{lucky.label()} gözleri kızardı, ÖFKELENDİ! Sırasını beklemeden saldırıyor!\n"
                    + await lucky.attack(unlucky, 'guclu'))
        if event == 4:
            lucky.power += 5
            return (head + f"{lucky.label()} etrafını altın bir aura sardı! Savaşta güçlendi!\n"
                    f"   Güç +5 (kalıcı) -> {lucky.power}")
        if event == 5:
            unlucky.hp = max(1, unlucky.hp - 40)
            return (head + f"Arena sarsıldı! {unlucky.label()} üstüne dev bir kaya düştü!\n"
                    f"   -40 sağlık!\n   " + unlucky.hp_bar())
        if Pokemon.pokemons.get(self.pokemon_trainer) is self:
            self.money += 30
            return (head + "Seyirciler coştu, arenaya altın yağdırıyorlar!\n"
                    f"   +30 altın! (Bakiye: {self.money})")
        return None

    COMMENTARY = ["SPİKER: İnanılmaz bir mücadele! Kimse geri adım atmıyor!",
                  "SPİKER: Seyirciler yerinde duramıyor!",
                  "SPİKER: {leader} şu anda üstün görünüyor!",
                  "SPİKER: {trailing} toparlanmak zorunda, yoksa bu iş bitecek!",
                  "SPİKER: Bu savaş tarihe geçecek, sayın seyirciler!"]

    BOT_NAMES = ["Bot_Ash", "Bot_Misty", "Bot_Brock", "Bot_Gary", "Bot_Dawn", "Bot_Red", "Bot_Blue"]

    async def find_opponent(self, legendary_chance=10):
        await self.load()
        enemy = create_random_pokemon(random.choice(self.BOT_NAMES), register=False)
        await enemy.load()
        title = "RAKİP BULUNDU!"
        if randint(1, 100) <= legendary_chance:
            enemy.legendary = True
            enemy.power += 30
            enemy.hp += 200
            enemy.max_hp = enemy.hp
            enemy.name = f"EFSANEVİ {enemy.name}"
            title = "OLAĞANÜSTÜ OLAY: EFSANEVİ BİR RAKİP ÇIKTI! (Yenersen +100 bonus altın)"
        self.opponent = enemy
        return (f"{title}\n"
                f"Rakip: {enemy.stats()}\n"
                f"Sen:   {self.stats()}\n"
                f"Savaşmak için !fight, başka rakip için !skip yaz.")

    async def skip_opponent(self):
        if self.opponent is None:
            return "Henüz bir rakibin yok. Rakip aramak için !find yaz."
        return f"{self.opponent.pokemon_trainer} geçildi.\n" + await self.find_opponent()

    async def fight(self):
        if self.opponent is None:
            return "Önce rakip bulmalısın: !find"
        if self.hp <= 0:
            return "Pokémon'un yenik durumda! Önce !feed veya !buy potion ile iyileştir."
        enemy, self.opponent = self.opponent, None
        return await Battle(self, enemy, 'fight').start()

    async def hunt(self, cost=20):
        if self.hp <= 0:
            return "Pokémon'un yenik durumda! Önce !feed veya !buy potion ile iyileştir."
        if self.money < cost:
            return f"Ava çıkmak için {cost} altın gerekiyor. Bakiyen: {self.money}"
        self.money -= cost

        wild = create_random_pokemon("Vahşi", register=False)
        await wild.load()
        await self.load()
        intro = ("Uzun otların arasında bir hışırtı... VAHŞİ BİR POKÉMON ÇIKTI!\n"
                 f"Vahşi: {wild.stats()}\nSen:   {self.stats()}\n")
        return intro + await Battle(self, wild, 'hunt').start()

class Wizard(Pokemon):
    MOVES = {
        **Pokemon.MOVES,
        'atestopu': {'name': 'Ateş Topu', 'mult': 2.0, 'acc': 60, 'hits': 1, 'type': 'fire'},
        'buz': {'name': 'Buz Oku', 'mult': 0.5, 'acc': 100, 'hits': 3, 'type': 'ice'},
    }

    async def feed(self, food=None):
        return await super().feed(food, feed_interval=10)

class Fighter(Pokemon):
    MOVES = {
        **Pokemon.MOVES,
        'kombo': {'name': 'Kombo Yumruk', 'mult': 0.5, 'acc': 90, 'hits': 4, 'type': 'fighting'},
        'tekme': {'name': 'Uçan Tekme', 'mult': 2.2, 'acc': 55, 'hits': 1, 'type': 'fighting'},
    }

    def power_bonus(self):
        bonus = randint(5, 15)
        return bonus, f"Dövüşçü Pokémon süper güç kullandı. Eklenen güç: {bonus}"

    async def feed(self, food=None):
        return await super().feed(food, hp_increase=20)

def create_random_pokemon(trainer, register=True):
    return random.choice([Pokemon, Wizard, Fighter])(trainer, register=register)


class Battle:
    EVENT_CHANCE = 15
    CATCH_CHANCE = 60

    def __init__(self, player, enemy, mode):
        self.player, self.enemy, self.mode = player, enemy, mode
        self.round = 1
        player.battle = self
        player.shield = enemy.shield = 0
        player.parrying = enemy.parrying = False

    def actions_text(self):
        return ("SIRA SENDE! Hamleni seç:\n"
                f"  !a <saldırı>   Saldır ({', '.join(self.player.MOVES)})\n"
                "  !parry         Savuştur: gelen hasarın %75'ini engelle, %30 şansla karşı saldırı\n"
                f"  !item <eşya>   Eşya kullan ({', '.join(self.player.BATTLE_ITEMS)})\n"
                "  !flee          Kaç\n"
                "  !durum         Durumu ve saldırıları gör")

    def status(self):
        return (f"\n---------- TUR {self.round} ----------\n"
                f"   {self.player.hp_bar()}\n   {self.enemy.hp_bar()}\n" + self.actions_text())

    async def start(self):
        p, e = self.player, self.enemy
        lines = ["=" * 50,
                 "SPİKER: Hoş geldiniz sayın seyirciler! Arena hıncahınç dolu!",
                 f"SPİKER: Sağ köşede {p.label()} - {p.type_text()} türü {type(p).__name__}, "
                 f"Güç {p.power}, Savunma {p.defense}, Hız {p.speed}!",
                 f"SPİKER: Sol köşede {e.label()} - {e.type_text()} türü {type(e).__name__}, "
                 f"Güç {e.power}, Savunma {e.defense}, Hız {e.speed}!",
                 "SPİKER: Bu bir sıra tabanlı savaş! Her hamle önemli..."]
        if e.speed > p.speed or (e.speed == p.speed and randint(0, 1)):
            lines.append(f"SPİKER: {e.label()} daha hızlı (Hız {e.speed} - {p.speed}), ilk hamle onun!")
            lines.append("=" * 50)
            lines.append(await self.bot_turn())
            end = self.check_end()
            if end:
                return "\n".join(lines + [end])
        else:
            lines.append(f"SPİKER: {p.label()} daha hızlı (Hız {p.speed} - {e.speed}), ilk hamle senin!")
            lines.append("=" * 50)
        lines.append(self.status())
        return "\n".join(lines)

    async def bot_turn(self):
        e, p = self.enemy, self.player
        e.parrying = False
        roll = randint(1, 100)
        if e.hp < e.max_hp * 0.3 and roll <= 40:
            return await e.attack(p, 'iyiles')
        if roll <= 15:
            e.parrying = True
            return f">> {e.label()} [PARRY] pozisyonu aldı! Bir sonraki saldırını savuşturmaya hazır!"
        return await e.attack(p)

    async def player_turn(self, action, arg=None):
        p, e = self.player, self.enemy
        lines = []
        if action == 'attack':
            if arg not in p.MOVES:
                return f"Bilinmeyen saldırı: {arg}\n{p.moves_text()}"
            p.parrying = False
            lines.append(await p.attack(e, arg))
        elif action == 'parry':
            p.parrying = True
            lines.append(f">> {p.label()} [PARRY] pozisyonu aldı! Bir sonraki saldırıyı savuşturmaya hazır!")
        elif action == 'item':
            ok, text = await p.use_item(arg)
            if not ok:
                return text
            p.parrying = False
            lines.append(f">> {p.label()} çantasından {arg} çıkardı!\n{text}")
        elif action == 'flee':
            if self.mode == 'fight':
                self.close()
                return f"{p.label()} maçtan çekildi! Ödül yok. SPİKER: Seyirciler yuhalıyor!"
            if randint(1, 100) <= 50:
                self.close()
                return f"{p.label()} çalıların arasından kaçmayı başardı!"
            p.parrying = False
            lines.append(f">> {p.label()} kaçmaya çalıştı ama {e.label()} yolunu kesti!")

        end = self.check_end()
        if end:
            return "\n".join(lines + [end])
        if randint(1, 100) <= self.EVENT_CHANCE:
            event = await p.random_event(e)
            if event:
                lines.append(event)
            end = self.check_end()
            if end:
                return "\n".join(lines + [end])
        lines.append(await self.bot_turn())
        end = self.check_end()
        if end:
            return "\n".join(lines + [end])

        self.round += 1
        if randint(1, 100) <= 25:
            leader, trailing = (p, e) if p.hp >= e.hp else (e, p)
            lines.append(random.choice(Pokemon.COMMENTARY).format(
                leader=leader.label(), trailing=trailing.label()))
        lines.append(self.status())
        return "\n".join(lines)

    def close(self):
        self.player.battle = None
        self.player.shield = self.enemy.shield = 0
        self.player.parrying = self.enemy.parrying = False

    def check_end(self):
        p, e = self.player, self.enemy
        if p.hp > 0 and e.hp > 0:
            return None
        self.close()
        winner, loser = (p, e) if e.hp <= 0 else (e, p)
        lines = ["", "=" * 50,
                 f"SPİKER: Ve {loser.label()} kalkamıyor... 1... 2... 3...!",
                 f"SPİKER: KAZANAN {winner.label()}! Ne muhteşem bir savaştı!",
                 "=" * 50]
        if winner is e:
            lines.append(f"KAYBETTİN! Pokémon'unu iyileştir: !feed / !buy potion")
            return "\n".join(lines)

        p.money += 50
        lines.append(f"KAZANDIN! +50 altın. Bakiye: {p.money}")
        if getattr(e, 'legendary', False):
            p.money += 100
            lines.append(f"Efsanevi rakibi yendin! +100 bonus altın. Bakiye: {p.money}")
        if self.mode == 'hunt':
            chance = self.CATCH_CHANCE + (20 if p.charm else 0)
            if randint(1, 100) > chance:
                lines.append(f"{e.name} yenildi ama kaçmayı başardı!")
            else:
                e.pokemon_trainer = p.pokemon_trainer
                e.money, e.charm, e.move_levels = p.money, p.charm, p.move_levels
                e.hp = e.max_hp
                Pokemon.pokemons[p.pokemon_trainer] = e
                lines.append(f"Tebrikler! {e.name} yakaladın, artık yeni Pokémon'un o!\n"
                             f"Yeni Pokémon: {e.stats()}")
        return "\n".join(lines)
