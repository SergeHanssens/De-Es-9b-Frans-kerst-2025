# Sims 4 Save Merger

Een tool om twee The Sims 4 save bestanden samen te voegen tot één werkend bestand.

## Probleem

Soms gebeurt het dat je nieuwere Sims 4 save niet alle data bevat die je verwacht:
- Je Sims zijn ouder geworden
- Maar sommige gebouwen zijn verdwenen
- Of objecten ontbreken

Je hebt dan een oudere save waar alles nog compleet is, maar daar zijn je Sims nog veel jonger.

## Oplossing

Deze tool combineert beide saves:
- **Basis**: De nieuwere save (met de actuele Sim-voortgang)
- **Aanvulling**: Ontbrekende data uit de oudere save (gebouwen, objecten, etc.)

## Installatie

Geen installatie nodig! Je hebt alleen Python 3.7+ nodig.

```bash
# Controleer je Python versie
python3 --version
```

## Gebruik

### Grafische Interface (Aanbevolen)

Start de GUI door te dubbelklikken op `run_merger.py` of via de terminal:

```bash
python3 -m sims4_save_merger
```

De GUI leidt je door het proces:
1. Selecteer de nieuwere save (basis bestand)
2. Selecteer de oudere save (bron voor ontbrekende data)
3. Analyseer de bestanden
4. Kies een output locatie
5. Klik op "Samenvoegen"

### Command Line Interface

```bash
# Analyseer een enkel save bestand
python3 -m sims4_save_merger.cli --analyze mysave.save

# Vergelijk twee save bestanden
python3 -m sims4_save_merger.cli --compare nieuwer.save ouder.save

# Voeg twee saves samen
python3 -m sims4_save_merger.cli nieuwer.save ouder.save merged.save
```

### Python API

```python
from sims4_save_merger import merge_saves, Sims4SaveMerger

# Snelle merge
result = merge_saves('nieuwer.save', 'ouder.save', 'output.save')
print(f"Succes: {result.success}")
print(f"Resources toegevoegd: {result.resources_from_older}")

# Met meer controle
merger = Sims4SaveMerger()
newer_stats, older_stats = merger.load_files('nieuwer.save', 'ouder.save')

# Bekijk wat er samengevoegd kan worden
comparison = merger.get_comparison_summary()
print(f"Resources toe te voegen: {comparison['resources_to_add']}")

# Voer de merge uit
result = merger.merge('output.save')
```

## Sims 4 Save Locatie

Je Sims 4 saves vind je meestal hier:

- **Windows**: `Documents\Electronic Arts\The Sims 4\saves`
- **Mac**: `Documents/Electronic Arts/The Sims 4/saves`
- **Linux**: `Documents/Electronic Arts/The Sims 4/saves`

## Technische Details

### DBPF Formaat

The Sims 4 gebruikt het DBPF (Database Packed File) formaat voor save bestanden. Dit is een containerformaat dat meerdere resources bevat:

- **SimInfo**: Informatie over je Sims
- **Household**: Huishouden data
- **Lot**: Perceel informatie
- **Zone**: Zone/buurt data
- **ObjectData**: Object plaatsingen
- **RelationshipData**: Relaties tussen Sims

### Merge Strategie

De standaard merge strategie:
1. Neem alle resources van de nieuwere save
2. Voeg resources toe die alleen in de oudere save bestaan
3. Bij conflicten (zelfde resource in beide bestanden): gebruik de nieuwere versie

## Waarschuwingen

- **Maak ALTIJD een backup** van je originele saves voordat je begint!
- De tool maakt automatisch een backup als je een bestaand bestand overschrijft
- Test het samengevoegde bestand eerst voordat je het als hoofdsave gebruikt
- Als het spel crasht na het laden, probeer dan een andere combinatie van saves

## Bestanden

```
sims4_save_merger/
├── __init__.py      # Package definitie
├── __main__.py      # Entry point
├── dbpf_parser.py   # DBPF bestandsformaat parser
├── merger.py        # Merge logica
├── gui.py           # Grafische interface
├── cli.py           # Command line interface
├── run_merger.py    # Launcher script
└── README.md        # Deze documentatie
```

## Vereisten

- Python 3.7 of hoger
- tkinter (voor GUI, meestal standaard meegeleverd)
- Geen externe packages nodig!

## Licentie

Vrij te gebruiken voor persoonlijk gebruik.
