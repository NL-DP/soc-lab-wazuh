# Dashboard "not ready" dopo il riavvio: l'indexer va in timeout all'avvio

## Sintomo
Dopo il riavvio della VM del manager la dashboard mostra "Wazuh dashboard server is not ready yet". `systemctl` indica `failed (Result: timeout)` per `wazuh-indexer` (la prima volta anche per `wazuh-manager`), mentre `wazuh-dashboard` risulta attivo. Mi è successo due volte, e la seconda ha corretto la mia prima soluzione.

## Diagnosi
**Primo riavvio.** Siccome la dashboard dipende dall'indexer, sono partito da lì. `journalctl -u wazuh-indexer` mostra:
```
wazuh-indexer.service: start operation timed out. Terminating.
```
Il 18 ottobre systemd ha avviato l'indexer alle 13:07:17, ma Java ha scritto la prima riga solo alle 13:09:55, e alle 13:10:18 sono scaduti i 3 minuti concessi. Nei riavvii precedenti l'avvio richiedeva circa 15 secondi.

La prima ipotesi era la mancanza di memoria, ma `dmesg` non mostra nessun processo ucciso dall'OOM killer. Ho concluso che fosse un boot lento sotto carico e ho alzato il timeout a 10 minuti.

**Secondo riavvio.** Con il timeout a 10 minuti l'indexer è andato in timeout comunque. Questa volta ho guardato la macchina mentre era ancora in avvio: `top` mostrava circa il 95% di I/O wait. La CPU non faceva calcoli, aspettava il disco. La causa non è la memoria e non è il carico di calcolo: è la saturazione dell'I/O al boot. Il tempo che serve all'indexer dipende da quanto il disco è lento in quel momento, e i 10 minuti non bastavano.

Cosa non so: perché il disco fosse così lento dopo il riavvio. Non ho guardato lo storage di Proxmox né l'I/O degli altri guest.

## Soluzione
Per rimettere in piedi il sistema ho avviato i servizi a mano in ordine, aspettando l'indexer:
```bash
sudo systemctl start wazuh-indexer
sleep 60
sudo systemctl start wazuh-manager
sudo systemctl restart wazuh-dashboard
```
Per i riavvii futuri ho portato il tempo massimo di avvio dell'indexer a 20 minuti (1200 secondi) con un drop-in di systemd, così non devo intervenire a ogni boot lento:
```bash
sudo mkdir -p /etc/systemd/system/wazuh-indexer.service.d
printf '[Service]\nTimeoutStartSec=1200\n' | sudo tee /etc/systemd/system/wazuh-indexer.service.d/timeout.conf
sudo systemctl daemon-reload
```
Verifica del valore in vigore (il default è 3 minuti per l'indexer e 45 secondi per il manager):
```bash
systemctl show wazuh-indexer wazuh-manager -p TimeoutStartUSec
```

## Lezione
Quando la dashboard dice "not ready" controllo prima l'indexer. Prima di dare la colpa alla RAM leggo i tempi nel log: quando parte il servizio e quando Java scrive la prima riga. Se l'avvio è lento guardo `top` durante il boot: un I/O wait alto indica che il collo di bottiglia è il disco, non la CPU né la memoria.

Ho sbagliato due volte la stima: prima ho escluso la RAM senza avere un'altra causa, poi ho scelto 10 minuti senza avere una misura. La VM del manager aveva 3,4 GB di RAM, sotto il minimo consigliato, e ora ne ha 8 GB; non l'ho verificato come causa di nessuno dei due timeout, l'ho corretto perché era comunque sotto il minimo. Da fare: capire perché l'I/O satura al boot (per esempio guardando lo storage di Proxmox) invece di limitarmi ad aspettare di più.

Collegati: [writeups/README.md](README.md), [docs/procedure.md](../docs/procedure.md), [docs/architecture.md](../docs/architecture.md).
