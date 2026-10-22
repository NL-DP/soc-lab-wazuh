# Script

## count-alerts.py
Conta gli alert di Wazuh per regola, con filtri su agent, intervallo di tempo, regola e livello. Legge `alerts.json` (un alert JSON per riga) in binario e salta le righe che non sono JSON valido, perché quel file contiene byte non testuali. È lo stesso tipo di conteggio che ho usato per la baseline nella sezione 4 di [docs/procedure.md](../docs/procedure.md): un primo tentativo con `grep` perdeva gli alert le cui descrizioni contengono virgolette.

Non ha dipendenze oltre a Python 3. Sul manager il file è `/var/ossec/logs/alerts/alerts.json` e si legge con `sudo`; ruota a mezzanotte, quindi i giorni passati stanno in `/var/ossec/logs/alerts/AAAA/Mese/`.

```bash
# tutti gli alert di win-01
sudo python3 count-alerts.py /var/ossec/logs/alerts/alerts.json --agent win-01

# la finestra della baseline: va confrontata con i 738 alert della procedura
python3 count-alerts.py alerts-2026-10-18.json --agent win-01 --from 2026-10-18T14:56 --to 2026-10-18T18:05

# solo le mie regole, a livello 8 o superiore
python3 count-alerts.py alerts.json --rule 100010 100011 100012 100013 100014 --min-level 8
```

Gli orari di `--from` e `--to` sono quelli locali del campo `timestamp` dell'alert. Lo script li confronta come testo, quindi vanno scritti nel formato `AAAA-MM-GGTHH:MM`.

Lo script serve per le misure su più giorni: è questo conteggio, ripetuto ogni giorno. Un test di regressione completo, che lancia anche le tecniche, non esiste ancora.

Collegati: [STRUTTURA.md](../STRUTTURA.md), [detections/samples/README.md](../detections/samples/README.md).
