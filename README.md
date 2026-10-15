# Allerta Emilia-Romagna (Home Assistant)

Integrazione **personalizzata (custom)** per Home Assistant che porta in HA le
**allerte meteo-idro-idrogeologiche** per area dell'Emilia-Romagna, lette dal
bollettino CAP di AllertaMeteoER. Una **area di allertamento per ogni voce**
configurabile.

> ## ⚠️ Disclaimer
>
> Questa integrazione è **NON ufficiale** e **non è affiliata, approvata o
> supportata** da AllertaMeteoER, dalla Regione Emilia-Romagna, da ARPAE o da
> Home Assistant.
>
> I dati provengono da servizi pubblici di terze parti e vengono forniti
> **"così come sono"**, **senza alcuna garanzia**. La **disponibilità del
> servizio**, la sua **continuità** e l'**esattezza dei dati non sono
> garantite** e possono cambiare o interrompersi in qualsiasi momento senza
> preavviso. **Non utilizzare questa integrazione per decisioni di sicurezza,
> protezione civile o emergenza**: fare sempre riferimento ai canali ufficiali.

## Fonte dati

| Organizzazione | Uso | Endpoint |
| --- | --- | --- |
| **AllertaMeteoER** | bollettino di allerta in formato **CAP 1.2** | `allertameteo.regione.emilia-romagna.it/o/xmlcap` |

Il documento CAP contiene **un solo `<alert>`** con una `note` unica e **una
`<info>` per area** (18 aree: `Emil-A1` … `Emil-H2`). Ogni area ha il proprio
livello (`event`), la validità (`onset`/`expires`) e 9 parametri di criticità.

Pagina ufficiale delle allerte e dei bollettini:
<https://allertameteo.regione.emilia-romagna.it/allerte-e-bollettini>

## Installazione (HACS)

1. In HACS apri il menu **⋮ → Custom repositories**.
2. Incolla l'URL di questo repository e scegli la categoria **Integration**.
3. Cerca **Allerta Emilia-Romagna** in HACS e premi **Download**.
4. **Riavvia** Home Assistant.

### Installazione manuale

Copia la cartella `custom_components/ha_allerta_er` in
`<config>/custom_components/ha_allerta_er` e riavvia Home Assistant.

## Configurazione

1. **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**.
2. Cerca **Allerta Emilia-Romagna**.
3. Scegli l'**area di allertamento** dall'elenco (letto dal feed live).
4. Ripeti l'aggiunta per **ogni area** desiderata: viene creata una voce di
   configurazione (e un dispositivo) per area, con il proprio intervallo di
   aggiornamento.

## Entità

Per ogni area viene creato un **dispositivo** (`Allerta ER A1`, …) con le
seguenti entità (`A1` = codice area senza il prefisso `Emil-`):

| Entità | Descrizione |
| --- | --- |
| `sensor.allerta_er_a1_evento` | Livello di allerta dell'area (`verde`, `giallo`, …) |
| `sensor.allerta_er_a1_nota` | Nota del bollettino (anteprima); **testo integrale** nell'attributo `testo` |
| `sensor.allerta_er_a1_inizio_validita` | Inizio validità (`onset`) |
| `sensor.allerta_er_a1_fine_validita` | Fine validità (`expires`) |
| `sensor.allerta_er_a1_inviato` | Data/ora di emissione (`sent`) |
| `sensor.allerta_er_a1_bollettino` | Numero bollettino (`identifier`, es. `162/2026`) — *diagnostica, disabilitata* |
| `sensor.allerta_er_a1_idraulico` | Criticità idraulica |
| `sensor.allerta_er_a1_idrogeologico` | Criticità idrogeologica |
| `sensor.allerta_er_a1_temporali` | Temporali |
| `sensor.allerta_er_a1_vento` | Vento |
| `sensor.allerta_er_a1_temperature_estreme` | Temperature estreme |
| `sensor.allerta_er_a1_neve` | Neve |
| `sensor.allerta_er_a1_pioggia_che_gela` | Pioggia che gela / ghiaccio |
| `sensor.allerta_er_a1_stato_mare` | Stato del mare — *disabilitata di default* |
| `sensor.allerta_er_a1_mareggiate` | Mareggiate — *disabilitata di default* |
| `binary_sensor.allerta_er_a1_allerta_attiva` | `on` se è in vigore un'allerta non verde |

### Nota lunga

Lo **stato** di un'entità di Home Assistant ha un limite **fisso di 255
caratteri**, quindi la nota del bollettino (che può essere lunga) è esposta
**per intero nell'attributo `testo`** di `sensor.*_nota`; lo stato mostra solo
un'anteprima. Per visualizzarla usa una *Markdown card*:

```jinja
{{ state_attr('sensor.allerta_er_a1_nota', 'testo') }}
```

## Mappa / link

Il documento CAP non contiene geometrie, quindi l'integrazione non crea
entità mappa. Su ogni dispositivo è presente il link **Allerte e Bollettini
Meteo** (pagina ufficiale della Regione Emilia-Romagna).

## Opzioni

Per ogni area (voce di configurazione → **Configura**):

- **Aggiornamento feed CAP** — default `3600` s (1 h), da `60` a `86400` s.

Il feed cambia poche volte al giorno: un intervallo ampio è più che
sufficiente e rispetta un servizio pubblico e gratuito. Per forzare subito un
aggiornamento usa il servizio `homeassistant.update_entity` sull'entità.

## Note

- Dati e disponibilità dipendono interamente dai servizi di terze parti.
- Progetto personale, **manutenzione e supporto non garantiti**.
- Marchi e nomi citati appartengono ai rispettivi proprietari.

## Licenza

[MIT](LICENSE)


## Esempi Lovelace

Puoi copiare questo blocco YAML direttamente in una card di tipo "Manuale" (Dashboard → Modifica → Aggiungi card → Manuale).

> **Nota:** l'esempio usa gli entity_id in italiano (`sensor.allerta_er_a1_evento`, `sensor.allerta_er_a1_nota`, ...), come prodotti da un'istanza HA in lingua italiana. Se la tua istanza ha la lingua inglese, gli ID saranno in inglese (es. `sensor.allerta_er_a1_event`): in quel caso sostituiscili con quelli effettivamente presenti nella tua istanza.

```yaml
type: grid
columns: 2
square: false
cards:
  # Nota del bollettino (testo integrale) — occupa due colonne
  - type: markdown
    title: Nota del bollettino di allerta meteo
    content: |
      {{ state_attr('sensor.allerta_er_a1_nota', 'testo') | default('Nessuna nota disponibile.') }}
    view_layout:
      column_span: 2

  # Stato generale dell'area — colonna sinistra
  - type: entities
    title: Allerta Emilia-Romagna — Emil-A1
    show_header_toggle: false
    entities:
      - entity: binary_sensor.allerta_er_a1_allerta_attiva
        name: Allerta attiva
      - entity: sensor.allerta_er_a1_evento
        name: Livello di allerta (evento)
      - entity: sensor.allerta_er_a1_inviato
        name: Emesso (sent)
      - entity: sensor.allerta_er_a1_inizio_validita
        name: Valido da (onset)
      - entity: sensor.allerta_er_a1_fine_validita
        name: Valido fino a (expires)

  # Criticità a scomparsa — colonna destra
  - type: vertical-stack
    cards:
      # Criticità IDRAULICA — mostrata solo se diversa da "verde"
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_idraulico
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_idraulico
          name: Idraulico
          icon: mdi:water

      # Criticità IDROGEOLOGICA — mostrata solo se diversa da "verde"
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_idrogeologico
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_idrogeologico
          name: Idrogeologico
          icon: mdi:landslide

      # Temporali — mostrata solo se diversa da "verde"
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_temporali
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_temporali
          name: Temporali
          icon: mdi:weather-lightning

      # Vento — mostrata solo se diversa da "verde"
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_vento
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_vento
          name: Vento
          icon: mdi:weather-windy

      # Temperature estreme — mostrata solo se diversa da "verde"
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_temperature_estreme
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_temperature_estreme
          name: Temperature estreme
          icon: mdi:thermometer-alert

      # Neve — mostrata solo se diversa da "verde"
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_neve
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_neve
          name: Neve
          icon: mdi:weather-snowy

      # Pioggia che gela — mostrata solo se diversa da "verde"
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_pioggia_che_gela
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_pioggia_che_gela
          name: Pioggia che gela
          icon: mdi:weather-snowy-rainy

      # Stato del mare — mostrata solo se diversa da "verde" (disabilitata di default)
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_stato_mare
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_stato_mare
          name: Stato del mare
          icon: mdi:waves

      # Mareggiate — mostrata solo se diversa da "verde" (disabilitata di default)
      - type: conditional
        conditions:
          - entity: sensor.allerta_er_a1_mareggiate
            state_not: "verde"
        card:
          type: entity
          entity: sensor.allerta_er_a1_mareggiate
          name: Mareggiate
          icon: mdi:wave
```


Le entità `stato_mare` e `mareggiate` sono **disabilitate di default** (non rilevanti per tutte le aree). Abilitele solo se l'area è costiera e vuoi visualizzarle.

Per altre aree (A2, B1, ..., H2) sostituisci `a1` con il codice corretto (es. `b2`, `d2`).
