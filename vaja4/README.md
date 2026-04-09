# Ekosistem Simulacija – MVP

## Namestitev

```bash
pip install -r requirements.txt
```

## Zagon

```bash
python main.py
```

## Struktura projekta

```
simulation/
├── main.py         ← vstopna točka, Simulation razred
├── config.py       ← vse nastavljive vrednosti
├── terrain.py      ← generiranje 4 vrst terena
├── entities.py     ← Fox, Rabbit, Clover razredi
├── ui.py           ← pygame UI (panel, drsniki, graf)
└── requirements.txt
```

## Upravljanje

| Akcija            | Tipka/gumb              |
|-------------------|-------------------------|
| Start simulacija  | ▶ Start                 |
| Pavza             | ⏸ Pause                 |
| Ponastavitev      | ↺ Reset                 |
| Pomik kamere      | W A S D ali puščice     |
| Izbira terena     | Reka / Jezero / Multi / Perlin |

## Tereni

1. **Reka** – sinusoidna reka čez karto
2. **Jezero** – eno eliptično jezero v sredini
3. **Multi** – 4–7 naključnih jezer
4. **Perlin** – Perlinov šum z višinskimi pasovi (zahteva knjižnico `noise`)

## Višinski pasovi (Perlin)

| Pas       | Delež |
|-----------|-------|
| Voda      | 40 %  |
| Pesek     | 2.5 % |
| Trava     | 35 %  |
| Gozd      | 15 %  |
| Gora      | 5 %   |
| Vrh gore  | 2.5 % |

## Lastnosti bitij

### Prioritetna vrsta potreb (najpomembnejša → najmanj)
1. **Razmnoževanje** – ko je prag `repro_drive` dosežen in ni prevelike žeje/lakote
2. **Žeja** – bitje išče vodo; smrt pri žeja ≥ 1.0
3. **Lakota** – bitje išče hrano; smrt pri lakota ≥ 1.0
4. **Tavanje** – ko ni nobene nujne potrebe

### Lisica (plenilec)
- Lovi plen glede na: bližino, počasnost in velikost zajca
- Živi do `fox_max_age` sekund

### Zajec (plen)
- Beži pred lisicami – izbere smer z najmanj plenilci
- Ne beži k drugi lisici

### Dedovanje
- Potomec podeduje povprečje lastnosti obeh staršev ± variacija
- Mutacija: 10 % verjetnost, da se lastnost spremeni za ±20 %

## Indikatorji nad bitji
- **Modra vrstica** = preostala voda (upada z žejo)
- **Rdeča vrstica** = preostala hrana (upada z lakoto)
