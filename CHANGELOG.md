# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il
progetto adotta il [Semantic Versioning](https://semver.org/lang/it/).

## [0.1.3] - 2026-11-15

### Fixed

- Download del feed CAP: fino a 3 tentativi con breve attesa (2 s / 5 s) in caso
  di errori TLS/rete (`ClientError`, `SSLError`, timeout) o risposta HTTP 5xx;
  avviso in log a ogni tentativo fallito. Riduce gli `unavailable` da errori
  transienti come `EOF occurred in violation of protocol`.

### Changed

- Dopo un aggiornamento fallito, il coordinator ripete il poll ogni 5 minuti
  finché il feed torna disponibile, poi ripristina l'intervallo configurato
  (es. 3600 s); messaggio informativo in log al recupero.

### Added

- Test su retry del fetch CAP e su intervallo di ripresa del coordinator.

## [0.1.2] - 2026-11-12

### Fixed

- Parser CAP: AllertaMeteoER (da circa l'11/11/2026) pubblica i livelli di
  criticità con `valueName` suffissati per fascia temporale (es.
  `IDRAULICO_2436`, `IDRAULICO_1224`) invece dei nomi storici (`IDRAULICO`, …).
  I sensori di fenomeno risultavano `unknown` (`Sconosciuto`). Normalizzazione
  al nome base, merge del livello più severo tra le fasce, default `verde` se il
  fenomeno manca del tutto; avviso in log per `valueName` non riconosciuti.

### Added

- Test unitari su `parse_cap` con fixture dal feed CAP live (11/11/2026).

## [0.1.0] - 2026-10-15

### Added

- Prima release.
- Config flow con selezione dell'area di allertamento (18 aree) letta dal feed
  CAP live di AllertaMeteoER; una voce di configurazione (e un dispositivo) per
  area.
- Sensori per area: livello di allerta (`event`), nota del bollettino (testo
  integrale in attributo, stato in anteprima), inizio/fine validità
  (`onset`/`expires`), emissione (`sent`) e numero bollettino (`identifier`,
  diagnostica disabilitata di default).
- Nove sensori di criticità: idraulico, idrogeologico, temporali, vento,
  temperature estreme, neve, pioggia che gela, stato del mare, mareggiate
  (questi ultimi due disabilitati di default).
- Binary sensor "allerta attiva".
- Cache condivisa del feed (60 s) e intervallo di aggiornamento configurabile
  (default 1 h).
- Supporto diagnostica.
