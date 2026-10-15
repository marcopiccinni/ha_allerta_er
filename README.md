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
