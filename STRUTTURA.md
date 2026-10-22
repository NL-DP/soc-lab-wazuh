# Struttura del progetto

Questa è la mappa del repo: dove sta ogni cosa, in che ordine conviene leggerla e con quali convenzioni è scritta. Si parte sempre dal [README](README.md).

## Le cartelle

```
soc-lab-wazuh/
├── README.md              risultati, due casi e limiti
├── STRUTTURA.md           questo file
├── docs/                  procedura, architettura e report di incidente
├── attack-emulation/      le tecniche emulate e i test eseguiti
├── detections/            regole personalizzate, risultati, alert di esempio e traduzioni Sigma
├── coverage/              copertura per tecnica e layer di ATT&CK Navigator
├── scripts/               script di supporto (conteggio degli alert)
├── config/                configurazione del gruppo lab
├── writeups/              i problemi incontrati, uno per file
└── evidence/              le schermate, numerate
```

## Cosa leggere e quando

- [README](README.md): cosa ho emulato, cosa ha visto Wazuh, cosa ho scritto io e quali sono i limiti.
- [docs/incident-report-01.md](docs/incident-report-01.md): la ricostruzione di un incidente dagli alert: timeline, triage, indicatori, verdetto.
- [writeups/](writeups/README.md): i problemi che ho incontrato e come li ho diagnosticati.
- [detections/README.md](detections/README.md): per ogni tecnica, cosa ha segnalato Wazuh di default e quale regola ho aggiunto.
- [detections/local_rules.xml](detections/local_rules.xml): le regole, pronte da copiare sul manager.
- [detections/samples/](detections/samples/README.md): un alert reale ripulito per ogni regola, per vedere i campi che leggono.
- [detections/sigma/](detections/sigma/README.md): tre regole tradotte in Sigma e cosa si perde nel passaggio.
- [coverage/](coverage/README.md): la copertura per tecnica in una tabella e in un layer di ATT&CK Navigator.
- [attack-emulation/README.md](attack-emulation/README.md): le cinque tecniche e i test lanciati.
- [docs/README.md](docs/README.md): l'indice della documentazione.
- [docs/procedure.md](docs/procedure.md): la procedura completa dalla rete ai test, per chi vuole riprodurre il lab.
- [docs/architecture.md](docs/architecture.md): macchine, gruppi Wazuh e stato dell'isolamento di rete.
- [scripts/](scripts/README.md): lo script che conta gli alert per regola, usato per la baseline.
- [config/lab-agent.conf](config/lab-agent.conf): la configurazione condivisa che fa leggere Sysmon agli agent del gruppo `lab`.
- [evidence/](evidence/): le schermate citate dai documenti.

## Tre percorsi di lettura

Con cinque minuti: il [report di incidente](docs/incident-report-01.md) e i write-up [03](writeups/03-falso-positivo-92213-psscriptpolicytest.md) e [04](writeups/04-lacuna-t1053-005-scheduled-task.md).

Con quindici minuti: il [README](README.md), la tabella di [detections/README.md](detections/README.md) e [local_rules.xml](detections/local_rules.xml).

Per rifare il lab: [architecture.md](docs/architecture.md), poi [procedure.md](docs/procedure.md) sezione per sezione, poi [local_rules.xml](detections/local_rules.xml).

## Convenzioni

Le schermate si chiamano `NN-argomento.png` e i numeri non vengono riutilizzati: mancano 03, 05 e 06 perché quelle schermate non le ho prese.

Le regole personalizzate vanno da 100010 a 100014. Il 100001 è occupato dall'esempio su sshd che Wazuh mette nel file di default, quindi il prossimo libero è il 100015. Il file nel repo contiene solo le mie regole; sul manager si aggiungono in coda a quel file.

I write-up si chiamano `NN-argomento.md` e hanno sempre la stessa traccia: sintomo, diagnosi, soluzione, lezione.

Nel repo le macchine si chiamano `wazuh-mgr`, `win-01`, `prod-01` e `prod-02`. I nomi veri non compaiono né nel testo né nelle schermate. Gli orari sono locali (CEST) e l'ora di un alert può differire da quella dell'evento anche di decine di secondi (vedi [detections/samples](detections/samples/README.md)).

Collegati: [README](README.md), [docs/README.md](docs/README.md).
