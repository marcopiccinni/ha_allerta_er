# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il
progetto adotta il [Semantic Versioning](https://semver.org/lang/it/).

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
