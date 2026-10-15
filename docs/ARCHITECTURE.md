# Architettura e API (riferimento verificato)

Documento di riferimento per sviluppatori. **Tutti i comportamenti qui
descritti sono stati verificati dal vivo**: non è necessario riprovare le API.

## Feed CAP di AllertaMeteoER

Endpoint: `https://allertameteo.regione.emilia-romagna.it/o/xmlcap`

- `GET` → **200**, `Content-Type: application/xml`, CAP **1.2**, ~**18.7 KB**
  (servito gzip dal CDN Varnish; header `Age`, `X-Cache: HIT`).
- **Nessun** `ETag` / `Last-Modified` → non è possibile una GET condizionale.
- **Nessun parametro di query utile**: `?area=Emil-A1` restituisce lo stesso
  documento. Percorsi `/o/xmlcap/1.2`, `/o/xmlcap_all`, `/o/xmlcaps`, `/o/xml`
  → **404**. Non riprovare.
- Namespace XML: `urn:oasis:names:tc:emergency:cap:1.2`.

### Struttura

Radice `<alert>` **unica** con:

- campi a livello alert: `identifier` (es. `162/2026`), `sent`, `status`,
  `msgType`, `source`, `scope` e **una sola `note`** (condivisa da tutte le
  aree; oggi ~90 caratteri, in allerta può essere molto lunga).
- **18 `<info>`**, uno per area: `Emil-A1, A2, B1, B2, C1, C2, D1, D2, D3, E1,
  E2, F1, F2, F3, G1, G2, H1, H2`.
- Ogni `<info>` contiene: `<area><areaDesc>` (il codice area), `<event>` (il
  livello di allerta, es. `VERDE`), **`<onset>`/`<expires>` propri**, e **9
  `<parameter>`** con coppie `valueName`/`value`:

  | valueName | chiave entità |
  | --- | --- |
  | `IDRAULICO` | `idraulico` |
  | `IDROGEOLOGICO` | `idrogeologico` |
  | `TEMPORALI` | `temporali` |
  | `VENTO` | `vento` |
  | `TEMPERATURE_ESTREME` | `temperature_estreme` |
  | `NEVE` | `neve` |
  | `GHIACCIO_PIOGGIA_CHE_GELA` | `pioggia_che_gela` |
  | `STATO_MARE` | `stato_mare` |
  | `MAREGGIATE` | `mareggiate` |

- I valori dei parametri **differiscono per area** e possono essere **vuoti**
  (`<value/>`): verificato su `STATO_MARE`, vuoto in 16 aree su 18 e valorizzato
  solo su `Emil-B2` e `Emil-D2`. Un valore vuoto → `None` → stato `unknown`.

### Timestamp

Formato CAP: `2026-10-15T00:00+02:00[Europe/Rome]`. Il suffisso IANA tra
parentesi quadre **non** è accettato da `datetime.fromisoformat`: va rimosso
(``value.split("[", 1)[0]``) prima del parsing. I valori sono già timezone-aware.

## Flusso dati

1. **Config flow** (`config_flow.py`): scarica il feed (tramite la cache
   condivisa) e presenta le 18 aree lette da `<areaDesc>` → crea l'entry con
   `unique_id = area:<codice>` (una entry per area). Se il feed non è
   raggiungibile → errore `cannot_connect` con possibilità di riprovare.
2. **Cache** (`cap.py`): `CapFeedCache` in `hass.data[DOMAIN]["feed"]` con TTL
   60 s. Tutte le aree provengono dallo **stesso** documento, quindi accessi
   ravvicinati producono **una sola** richiesta HTTP (protetta da `asyncio.Lock`).
3. **Coordinator** (`coordinator.py`): un `AreaAlertCoordinator` per entry, con
   `update_interval` dalla propria opzione (default 3600 s). Estrae la propria
   `<info>` dal feed e produce un `AreaAlertData`. Se l'area sparisce dal feed
   → `UpdateFailed` (entità `unavailable`).
4. **Entità** (`sensor.py`, `binary_sensor.py`): 6 sensori di base + 9 parametri
   + 1 binary sensor. Nome dispositivo `Allerta ER <label>` dove `<label>` è il
   codice area senza il prefisso `Emil-` (→ `sensor.allerta_er_a1_evento`).

## Limite di 255 caratteri

- Lo **stato** di un'entità HA è limitato a **255 caratteri** (core
  `homeassistant/core.py`, `MAX_STATE_LENGTH = 255`; colonna DB
  `state = Column(String(255))`). Non aggirabile.
- Gli **attributi** non hanno il limite di 255; il recorder tronca/scarta il
  blob attributi solo oltre **16384 byte**. La `note` completa (tipicamente
  1-3 KB) è quindi esposta come attributo `testo` di `sensor.*_nota`, mentre
  lo stato mostra un'anteprima troncata a 250 caratteri + `…`.

## Default (in `const.py`)

| Costante | Valore | Note |
| --- | --- | --- |
| `DEFAULT_SCAN_INTERVAL` | 3600 s | intervallo feed |
| `MIN_SCAN_INTERVAL` / `MAX_SCAN_INTERVAL` | 60 / 86400 s | limiti opzione |
| `FEED_TTL` | 60 s | cache condivisa feed |

## Invarianti

- Una config entry = una area (`unique_id` = `area:<codice>`).
- Un dispositivo per area; `unique_id` entità = `<codice>_<key>`.
- Le aree sono lette dal feed, mai hardcodate.
- `stato_mare` e `mareggiate` sono disabilitate di default (non tutte le aree
  sono costiere).
- Il servizio è di terzi: nessuna garanzia di disponibilità (vedi disclaimer).
