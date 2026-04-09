# Vaja 4 – Ekosistem Simulacija

> Simulacija ekosistema: Lisica (plenilec) – Zajec (plen) – Radič (hrana)

## Namestitev

```bash
pip install -r requirements.txt
```

## Zagon

```bash
cd vaja4
python main.py
```

## Struktura projekta

```
vaja4/
├── main.py          ← vstopna točka + razred Simulation (game loop, update, history)
├── config.py        ← vse nastavljive vrednosti na enem mestu
├── terrain.py       ← generiranje 4 matematičnih vrst terena
├── entities.py      ← Fox, Rabbit, Clover (dedovanje, mutacija, lov, beg)
├── ui.py            ← pygame UI (drsniki, graf populacije, statistika, kamera)
└── requirements.txt ← pygame, numpy, noise
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
| **Žeja** | narašča glede na hitrost bitja; smrt pri žeja ≥ 1.0 |
| **Razmnoževanje** | prag `repro_drive`; potrebna sta M + F |
| **Starost** | bitje umre po `max_age` sekundah |
| **Zaznava** | radij zaznavanja okolice (`sense_radius`) |
| **Spol** | M ali F; pogoj za razmnoževanje |
| **Hitrost** | vpliva na porabo žeje |
| **Velikost** | vpliva na porabo lakote; upošteva se pri izbiri partnerja/plena |
| **Variacija** | ±10 % odstopanje od baznih vrednosti pri rojstvu |

### Prioritetna vrsta potreb

```
Žeja  →  Lakota  →  Razmnoževanje  →  Tavanje
```

> Razmnoževanje je blokirano pri visoki žeji (> 60 %) ali lakoti (> 70–80 %).

### Lisica (plenilec)

- Lovi najboljši plen z oceno: `razdalja / (velikost × hitrostni_faktor)`
  → prednost bližjemu, večjemu in počasnejšemu zajcu
- Indikatorji: oranžen obroč zaznavanja, modra (voda) in rdeča (lakota) vrstica

### Zajec (plen)

- Beži pred vsemi bližnjimi lisicami hkrati (povprečni vektor stran)
- Preveri, da ne beži k drugi oddaljenejši lisici – v tem primeru zarotira smer
- Pase radič (pojeden ostane kot bleda pika, se ne obnavlja)
- Indikatorji: rumen obroč zaznavanja, modra in rdeča vrstica

### Radič (hrana)

- Hrana za zajce; po zaužitju postane prosojno vijolična pika
- Se **ne obnavlja** – zaloga samo upada

---

## Dedovanje in mutacija

- **Dedovanje:** potomec podeduje povprečje lastnosti obeh staršev, nato aplicira variacija
- **Mutacija:** 10 % verjetnost pri vsakem rojstvu, da se lastnost naključno spremeni za ±20 %
- Dedovane lastnosti: hitrost, velikost, zaznava, max. lakota, max. žeja, max. starost

---

## Uporabniški vmesnik

- **Levo:** simulacijska površina (700 × 547 px) s kamero
- **Desno zgoraj:** graf populacije v realnem času (lisice / zajci / radič)
- **Desno spodaj:** statistika (število bitij, korak, čas)
- **Spodaj 3 stolpci:** nastavitve terena + start/pavza/reset | lastnosti lisice | lastnosti zajca
- **Pas hitrosti:** hitrost simulacije 0.2× – 15×
- **Pas mutacije:** verjetnost mutacije 0 – 50 %

Parametri lisice, zajca in radiča so nastavljivi samo pred zagonom.  
Hitrost simulacije je nastavljiva med izvajanjem.

---

## Implementirane zahteve

| Sklop | % | Status |
|---|---|---|
| Osnovna simulacija (teren, bitja, potrebe, spol, starost, zaznava, variacija) | 60 % | ✅ implementirano |
| Perlinov šum + 6 višinskih pasov z razmerji | 10 % | ⚠️ 6 pasov vizualno prisotnih, Perlinov šum ni implementiran |
| Lov in beg (izbira plena, beg pred skupino, izogibanje) | 10 % | ✅ implementirano |
| Dedovanje in mutacija | 5 % | ✅ implementirano |
| Uporabniški vmesnik | 15 % | ✅ implementirano |
