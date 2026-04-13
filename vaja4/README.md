# Vaja 4 – Ekosistem Simulacija

> Simulacija ekosistema: Lisica (plenilec) – Zajec (plen) – Radič (hrana)

## Namestitev

```bash
pip install pygame numpy
```

## Zagon

```bash
cd vaja4
python main.py
```

## Struktura projekta

```
vaja4/
├── main.py        ← vstopna točka + razred Simulation (game loop, update, history)
├── config.py      ← vse nastavljive vrednosti na enem mestu
├── terrain.py     ← generiranje 4 matematičnih vrst terena
├── entities.py    ← Fox, Rabbit, Clover (dedovanje, mutacija, lov, beg)
└── ui.py          ← pygame UI (drsniki, graf populacije, statistika, kamera)
```

---

## Upravljanje

| Akcija | Tipka / gumb |
|---|---|
| Zagon simulacije | ▶ Start |
| Pavza / nadaljevanje | ⏸ Pavza |
| Ponastavitev | ↺ Reset |
| Pomik kamere | W A S D ali puščice |
| Izhod | ESC |

---

## Tereni (4 matematični)

| # | Ime | Opis |
|---|---|---|
| 1 | **Reka** | Vijugava sinusoidna reka z gozdnimi bregovi in peščenimi brežinami |
| 2 | **Jezero** | Organsko oblikovano jezero z obalnimi pasovi in satelitskim ribnikom |
| 3 | **Delta** | Rečna delta z vejastimi rokavi, peščenimi otočki in gozdnimi pasovi |
| 4 | **Dolina** | Gorska dolina s koncentričnimi pasovi (gora/gozd/trava), centralnim jezerom in potokom |

Teren je mogoče izbrati pred zagonom – po kliku se takoj prikaže predogled.

### Višinski pasovi (vsi tereni skupaj)

| Pas | Barva | Prehodnost |
|---|---|---|
| Voda | modra | ❌ neprehodna – pitje ob robu |
| Pesek | peščena | ✅ |
| Trava | zelena | ✅ |
| Gozd | temno zelena | ✅ |
| Gora | siva | ✅ (samo Dolina) |
| Vrh gore | bela | ✅ (samo Dolina) |

---

## Bitja

### Skupne lastnosti (Lisica in Zajec)

| Lastnost | Opis |
|---|---|
| **Lakota** | narašča glede na velikost bitja; smrt pri lakota ≥ 1.0 |
| **Žeja** | narašča glede na hitrost bitja; **poveča se, ko je bitje lačno** |
| **Razmnoževanje** | prag `repro_drive`; potrebna sta M + F; blokirano samo pri kritični žeji/lakoti |
| **Starost** | bitje umre po `max_age` sekundah; kaže kako dolgo je preživelo |
| **Zaznava** | radij zaznavanja okolice (`sense_radius`) |
| **Spol** | M ali F; pogoj za razmnoževanje |
| **Hitrost** | vpliva na porabo žeje |
| **Velikost** | vpliva na porabo lakote; upošteva se pri izbiri partnerja/plena (večje je boljše) |
| **Variacija** | ±10 % odstopanje od baznih vrednosti pri rojstvu |

### Prioritetna vrsta potreb

```
[Zajec: Beg pred plenilci]  →  Razmnoževanje  →  Žeja  →  Lakota  →  Tavanje
```

> Razmnoževanje je absolutna prioriteta – ob veliki želji bitje preneha iskati vodo in hrano.
> Blokirano je samo pri kritični žeji (> 85 %) ali lakoti (> 90 %) – tik pred smrtjo.
> Ko bitju zmanjka hrane, se poveča potreba po vodi (thirst_mult = 1 + 0.5 × hunger).
> Za zajca je beg pred plenilci absolutna prioriteta (pred vsem ostalim).

### Lisica (plenilec)

- Lovi najboljši plen z oceno: `razdalja / (velikost × hitrostni_faktor)`
  → prednost bližjemu, večjemu in počasnejšemu zajcu
- Indikatorji: oranžen obroč zaznavanja, modra (žeja) in rdeča (lakota) vrstica

### Zajec (plen)

- Beži pred vsemi bližnjimi lisicami hkrati (povprečni vektor stran)
- Preveri, da ne beži k drugi oddaljenejši lisici – v tem primeru zarotira smer bega
- Pase radič (pojeden ostane kot bleda pika, se ne obnavlja)
- Indikatorji: rumen obroč zaznavanja, modra in rdeča vrstica

### Radič (hrana)

- Hrana za zajce; po zaužitju postane prosojno vijolična pika
- Se **ne obnavlja** – zaloga samo upada

---

## Dedovanje in mutacija

- **Dedovanje:** potomec podeduje povprečje lastnosti obeh staršev, nato aplicira variacija (±10 %)
- **Mutacija:** 10 % verjetnost pri vsakem rojstvu, da se lastnost naključno spremeni za ±20 %
- Dedovane lastnosti: hitrost, velikost, zaznava, max. lakota, max. žeja, max. starost

---

## Uporabniški vmesnik

- **Levo:** simulacijska površina (700 × 547 px) s kamero
- **Desno zgoraj:** graf populacije v realnem času (lisice / zajci / radič)
- **Desno spodaj:** statistika – število bitij, korak, čas
- **Spodaj 3 stolpci:**
  - *Stolpec 1:* nastavitve (start/pavza/reset, izbira terena, vizualizacija, drsnik radiča)
  - *Stolpec 2:* lastnosti lisice (hitrost, velikost, zaznava, …)
  - *Stolpec 3:* lastnosti zajca (hitrost, velikost, zaznava, …)
- **Povprečna statistika živali** (pod drsnikom radiča): starost, velikost, lakota, žeja, hitrost, zaznava, rojstva – za lisice in zajce
- **Novorojene živali** so 4 sekunde prikazane v rožnati barvi
- **Pas hitrosti simulacije:** 0.2× – 15×
- **Pas mutacije:** verjetnost 0 – 50 %, količina 0 – 50 %

Parametri lisice, zajca in radiča so nastavljivi samo pred zagonom.
Hitrost simulacije in mutacija sta nastavljivi med izvajanjem.

---

## Implementirane zahteve

| Sklop | % | Status |
|---|---|---|
| Teren (voda/kopno, 4 tipi, prehodnost, pitje ob vodi) | 60 % | ✅ |
| Plenilec + plen (lakota, žeja, razmnoževanje, starost, zaznava, spol, hitrost, velikost, variacija, prioritetna vrsta, žeja↑ ob lakoti) | | ✅ |
| Perlinov šum + 6 višinskih pasov z razmerji | 10 % | ❌ ni implementirano |
| Lov (izbira plena: bližji/večji/počasnejši) in beg (izogibanje skupini, ne beži k drugi lisici) | 10 % | ✅ |
| Dedovanje (povprečje staršev + variacija) in mutacija (10 % / ±20 %) | 5 % | ✅ |
| Uporabniški vmesnik (nastavitve, izbira terena, kamera, mutacija) | 15 % | ✅ |
