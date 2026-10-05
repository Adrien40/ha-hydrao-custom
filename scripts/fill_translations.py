"""Add the 5 keys missing from the non-English/French translation files.

Usage: python scripts/fill_translations.py
Idempotent: existing values are never overwritten.
"""

import json
from pathlib import Path

DIR = (
    Path(__file__).parent.parent
    / "custom_components"
    / "hydrao_custom"
    / "translations"
)

# lang: (address hint, min temp hint, cold shower duration, time to comfort)
T = {
    "cs": (
        "Bluetooth MAC adresa zařízení, například AA:BB:CC:DD:EE:FF. Dvojtečky, pomlčky i mezery jsou povoleny.",
        "Voda s touto teplotou nebo vyšší se považuje za příjemnou, chladnější voda se považuje za zbytečně spotřebovanou. Od 0 do 50 °C. Používá pouze Home Assistant, nikdy se neodesílá do zařízení.",
        "Doba sprchování studenou vodou",
        "Doba do dosažení komfortní teploty",
    ),
    "da": (
        "Enhedens Bluetooth MAC-adresse, for eksempel AA:BB:CC:DD:EE:FF. Kolon, bindestreg og mellemrum accepteres.",
        "Vand ved eller over denne temperatur regnes som behageligt, vand under den regnes som spildt. Mellem 0 og 50 °C. Bruges kun af Home Assistant og sendes aldrig til enheden.",
        "Badevarighed med koldt vand",
        "Tid til komforttemperatur",
    ),
    "de": (
        "Bluetooth-MAC-Adresse des Geräts, zum Beispiel AA:BB:CC:DD:EE:FF. Doppelpunkte, Bindestriche und Leerzeichen werden akzeptiert.",
        "Wasser ab dieser Temperatur gilt als angenehm, kälteres Wasser gilt als verschwendet. Zwischen 0 und 50 °C. Wird nur von Home Assistant verwendet und nie an das Gerät gesendet.",
        "Duschdauer mit kaltem Wasser",
        "Zeit bis zur Komforttemperatur",
    ),
    "el": (
        "Διεύθυνση Bluetooth MAC της συσκευής, για παράδειγμα AA:BB:CC:DD:EE:FF. Γίνονται δεκτά άνω και κάτω τελεία, παύλες και κενά.",
        "Το νερό σε αυτή τη θερμοκρασία ή υψηλότερη θεωρείται άνετο, ενώ το νερό κάτω από αυτήν θεωρείται σπαταλημένο. Από 0 έως 50 °C. Χρησιμοποιείται μόνο από το Home Assistant και δεν στέλνεται ποτέ στη συσκευή.",
        "Διάρκεια ντους με κρύο νερό",
        "Χρόνος έως τη θερμοκρασία άνεσης",
    ),
    "es": (
        "Dirección MAC Bluetooth del dispositivo, por ejemplo AA:BB:CC:DD:EE:FF. Se aceptan dos puntos, guiones y espacios.",
        "El agua a esta temperatura o por encima se considera confortable; por debajo se considera desperdiciada. Entre 0 y 50 °C. Solo lo usa Home Assistant y nunca se envía al dispositivo.",
        "Duración de la ducha con agua fría",
        "Tiempo hasta la temperatura de confort",
    ),
    "hr": (
        "Bluetooth MAC adresa uređaja, na primjer AA:BB:CC:DD:EE:FF. Dopuštene su dvotočke, crtice i razmaci.",
        "Voda na ovoj temperaturi ili višoj smatra se ugodnom, a hladnija voda smatra se potrošenom uzalud. Od 0 do 50 °C. Koristi je samo Home Assistant i nikada se ne šalje uređaju.",
        "Trajanje tuširanja hladnom vodom",
        "Vrijeme do ugodne temperature",
    ),
    "hu": (
        "Az eszköz Bluetooth MAC-címe, például AA:BB:CC:DD:EE:FF. Kettőspont, kötőjel és szóköz is elfogadott.",
        "Az ennél a hőmérsékletnél melegebb víz kényelmesnek számít, az ennél hidegebb víz elpazarolt. 0 és 50 °C között. Csak a Home Assistant használja, az eszközre soha nem kerül elküldésre.",
        "Hideg vizes zuhanyzás időtartama",
        "Idő a komfort hőmérsékletig",
    ),
    "it": (
        "Indirizzo MAC Bluetooth del dispositivo, ad esempio AA:BB:CC:DD:EE:FF. Sono accettati due punti, trattini e spazi.",
        "L'acqua a questa temperatura o superiore è considerata confortevole, quella più fredda è considerata sprecata. Tra 0 e 50 °C. Usata solo da Home Assistant, mai inviata al dispositivo.",
        "Durata della doccia con acqua fredda",
        "Tempo per raggiungere la temperatura di comfort",
    ),
    "nb": (
        "Enhetens Bluetooth MAC-adresse, for eksempel AA:BB:CC:DD:EE:FF. Kolon, bindestrek og mellomrom godtas.",
        "Vann ved eller over denne temperaturen regnes som behagelig, vann under regnes som bortkastet. Mellom 0 og 50 °C. Brukes bare av Home Assistant og sendes aldri til enheten.",
        "Dusjvarighet med kaldt vann",
        "Tid til komforttemperatur",
    ),
    "nl": (
        "Bluetooth MAC-adres van het apparaat, bijvoorbeeld AA:BB:CC:DD:EE:FF. Dubbele punten, streepjes en spaties worden geaccepteerd.",
        "Water op of boven deze temperatuur geldt als comfortabel, water eronder geldt als verspild. Tussen 0 en 50 °C. Wordt alleen door Home Assistant gebruikt en nooit naar het apparaat gestuurd.",
        "Douchetijd met koud water",
        "Tijd tot comforttemperatuur",
    ),
    "pl": (
        "Adres MAC Bluetooth urządzenia, na przykład AA:BB:CC:DD:EE:FF. Dwukropki, myślniki i spacje są akceptowane.",
        "Woda o tej temperaturze lub wyższej jest uznawana za komfortową, a chłodniejsza za zmarnowaną. Od 0 do 50 °C. Używane tylko przez Home Assistant i nigdy nie wysyłane do urządzenia.",
        "Czas trwania prysznica z zimną wodą",
        "Czas do osiągnięcia temperatury komfortu",
    ),
    "pt-BR": (
        "Endereço MAC Bluetooth do dispositivo, por exemplo AA:BB:CC:DD:EE:FF. Dois-pontos, hífens e espaços são aceitos.",
        "A água nesta temperatura ou acima é considerada confortável; abaixo dela, é considerada desperdiçada. Entre 0 e 50 °C. Usado apenas pelo Home Assistant e nunca enviado ao dispositivo.",
        "Duração do banho com água fria",
        "Tempo até a temperatura de conforto",
    ),
    "pt": (
        "Endereço MAC Bluetooth do dispositivo, por exemplo AA:BB:CC:DD:EE:FF. Dois pontos, hífenes e espaços são aceites.",
        "A água a esta temperatura ou acima é considerada confortável; abaixo dela é considerada desperdiçada. Entre 0 e 50 °C. Usado apenas pelo Home Assistant e nunca enviado para o dispositivo.",
        "Duração do duche com água fria",
        "Tempo até à temperatura de conforto",
    ),
    "ru": (
        "Bluetooth MAC-адрес устройства, например AA:BB:CC:DD:EE:FF. Допускаются двоеточия, дефисы и пробелы.",
        "Вода с этой температурой или выше считается комфортной, более холодная вода считается потраченной впустую. От 0 до 50 °C. Используется только Home Assistant и никогда не отправляется на устройство.",
        "Продолжительность душа с холодной водой",
        "Время до комфортной температуры",
    ),
    "sv": (
        "Enhetens Bluetooth MAC-adress, till exempel AA:BB:CC:DD:EE:FF. Kolon, bindestreck och mellanslag accepteras.",
        "Vatten vid eller över denna temperatur räknas som behagligt, vatten under den räknas som slösat. Mellan 0 och 50 °C. Används bara av Home Assistant och skickas aldrig till enheten.",
        "Duschtid med kallt vatten",
        "Tid till komforttemperatur",
    ),
    "zh-Hans": (
        "设备的蓝牙 MAC 地址，例如 AA:BB:CC:DD:EE:FF。可使用冒号、连字符和空格。",
        "达到或高于此温度的水视为舒适，低于此温度的水视为浪费。范围为 0 至 50 °C。仅由 Home Assistant 使用，不会发送到设备。",
        "冷水淋浴时长",
        "达到舒适温度所需时间",
    ),
    "zh-Hant": (
        "裝置的藍牙 MAC 位址，例如 AA:BB:CC:DD:EE:FF。可使用冒號、連字號和空格。",
        "達到或高於此溫度的水視為舒適，低於此溫度的水視為浪費。範圍為 0 至 50 °C。僅由 Home Assistant 使用，不會傳送到裝置。",
        "冷水淋浴時長",
        "達到舒適溫度所需時間",
    ),
}

for lang, (addr, thr, cold, ttc) in T.items():
    path = DIR / f"{lang}.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    steps = d["config"]["step"]
    steps["user"].setdefault("data_description", {}).setdefault("address", addr)
    steps["user"]["data_description"].setdefault("min_temp_threshold", thr)
    steps["bluetooth_confirm"].setdefault("data_description", {}).setdefault(
        "min_temp_threshold", thr
    )
    sensors = d["entity"]["sensor"]
    sensors.setdefault("shower_duration_cold", {"name": cold})
    sensors.setdefault("time_to_comfort", {"name": ttc})
    path.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("updated", lang)
