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

### Kako se vsak teren generira

#### 1 – Reka

**Korak 1 – Osnovno ozadje:**
Mreža se najprej razdeli na dve polovici. Zgornja polovica dobí tip GOZD, spodnja TRAVA. To je samo izhodišče – reka ga bo prekinila.

**Korak 2 – Parametri reke:**
Naključno se določijo: širina reke (5–8 celic), amplituda vijuganja (1/5 višine karte), začetna faza in vertikalni položaj sredine. Vsaka generacija reke je zato drugačna.

**Korak 3 – Risanje reke stolpec po stolpec:**
Za vsak stolpec `c` se izračuna vrstica, kjer leži sredina reke:
```
mid = center + amplitude × sin(freq × c + phase)
```
Sin funkcija povzroči, da reka vijuga levo-desno. Okoli te vrednosti `mid` se narišejo trije koncentrični pasovi:
- najprej travnati koridor (8 celic na vsako stran) – gozdne celice se spremenijo v travo
- nato peščene brežine (1 celica na vsako stran vode)
- nato sama voda (v sredini, široka `river_w` celic)

**Korak 4 – Gozdni otočki:**
Na koncu se vsaka travnata celica z 7 % verjetnostjo naključno spremeni v gozd – to ustvari naravno videz posameznih dreves v travniku.

---

#### 2 – Jezero

**Korak 1 – Osnovno ozadje:**
Celotna mreža se nastavi na GOZD.

**Korak 2 – Oblika jezera:**
Določi se središče jezera (malo levo od sredine karte) in radija elipse (vodoravni in navpični). Jezero torej ni krog, ampak elipsa.

**Korak 3 – Deformacija elipse:**
Za vsako celico se najprej izračuna, kako daleč je od središča jezera glede na elipso (vrednost `d`). Čista elipsa bi izgledala preveč umetno, zato se ji doda kotna variacija – izračuna se kot celice glede na središče (`θ`) in doda vsota treh sinusnih valov z različnimi frekvencami:
```
eff = d + 0.10×sin(3θ) + 0.07×cos(5θ) + 0.04×sin(7θ)
```
Ti sinusi "porinejo" rob jezera na nekaterih kotih ven, na drugih noter – jezero dobi nepravilno, naravno obliko.

**Korak 4 – Dodelitev tipa glede na razdaljo:**
Na podlagi vrednosti `eff` (efektivna razdalja) se vsaki celici dodeli tip:
- `eff < 0.88` → VODA (jedro jezera)
- `eff < 1.05` → PESEK (obala)
- `eff < 1.65` → TRAVA (travnik ob jezeru)
- ostalo → GOZD (zunanjost)

**Korak 5 – Ribnik:**
V zgornjem desnem kotu se z enako elipsno logiko (brez deformacije) doda manjši ribnik z ozkim peščenim pasom.

**Korak 6 – Gozdne jase:**
Vsaka gozdna celica se z 10 % verjetnostjo naključno spremeni v travo.

---

#### 3 – Delta

**Korak 1 – Osnovno ozadje:**
Celotna mreža se nastavi na TRAVA.

**Korak 2 – Določitev kanalov:**
Naključno se določi število kanalov (4–6) in skupna izvorna točka na vrhu karte (malo naključno zamaknjeno od sredine). Vsak kanal dobi vrednost `spread` – to je njegov odmik od sredine, od leve do desne.

**Korak 3 – Risanje kanalov vrstico po vrstico:**
Za vsak kanal in vsako vrstico se izračuna, kje leži sredina kanala v tej vrstici. Kanal se postopoma oddaljuje od skupne točke z kvadratno funkcijo:
```
target_c = source_c + spread × cols × 0.48 × t²
```
kjer je `t = r / rows` (vrednost med 0 in 1, ki pove kako daleč smo od vrha). Kvadratni `t²` pomeni, da se kanali razlivajo počasi na vrhu in hitro na dnu. Širina kanala prav tako narašča z `t`.

Za glajenje se nova pozicija kanala izračuna kot 65 % ciljne in 35 % prejšnje vrednosti – kanal ne skoči nenadoma.

**Korak 4 – Peščena obala:**
Ko so vsi kanali postavljeni, se preveri vsaka travnata celica. Če ima vsaj enega od osmih sosedov vodo, se ta celica spremeni v pesek – dobimo naravno peščeno obalo.

**Korak 5 – Gozdni pasovi:**
Vsaka preostala travnata celica se z 10 % verjetnostjo naključno spremeni v gozd.

---

#### 4 – Dolina

**Korak 1 – Radialni pasovi:**
Za vsako celico se izračuna njena razdalja od središča karte in se normalizira (vrednost med 0 in 1):
```
d = hypot(c - cx, r - cy) / max_d
```
Čista radialna razdalja bi dala popolne koncentrične kroge. Da bi teren izgledal bolj naraven, se doda šum:
```
šum = 0.07×sin(5θ + 1.2) + 0.05×cos(7θ − 0.8) + 0.04×sin(c×0.08 + r×0.06)
```
Prva dva člena sta odvisna od kota celice (`θ`), tretji pa od njenih absolutnih koordinat – to ustvari asimetrično, nepravilno obliko.

Na podlagi skupne vrednosti `dn = d + šum` se celici dodeli tip:
- `dn < 0.18` → TRAVA (dolina v sredini)
- `dn < 0.44` → GOZD (gozdni pas)
- `dn < 0.63` → GORA (pobočje)
- ostalo → VRH GORE (mrzli vrhovi na robovih)

**Korak 2 – Centralno jezero:**
Neodvisno od zgornjega se izračuna absolutna razdalja vsake celice od središča. Celice znotraj 10 % polmera karte postanejo voda, celice med 10 % in 14 % postanejo pesek (jezerska obala).

**Korak 3 – Potok:**
Izbere se naključna smer (kot med 0 in 360°). Iz središča jezera se korak po korak pomika "korak" v to smer, z majhnim sinusnim nihanjem (da ni povsem ravna črta). Vsaka celica na poti (razen gor in vrhov) postane voda. Ko je potok narisan, dobijo vse travnate in gozdne celice ob vodi peščen rob.

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
