# Report di incidente 01: due account locali creati su win-01

Questo è un incidente emulato: i comandi sono i test T1136.001-4 e -5 di Atomic Red Team, che ho lanciato io il 18 ottobre 2026. Lo scrivo come lo scriverebbe un analista, partendo dagli alert e non dalla conoscenza di quello che ho eseguito, per esercitarmi nella ricostruzione. La fonte è `alerts.json` del manager, filtrato su `win-01` tra le 19:20 e le 19:38 (CEST): 32 alert, di cui 24 riguardano questo incidente.

## Sintesi
Tra le 19:28 e le 19:30 sono stati creati e cancellati due account locali su `win-01`. Il primo con `net user /add` da cmd, il secondo da PowerShell. Il primo è stato segnalato da due fonti (il processo e l'audit di Security), il secondo solo dall'audit. Ogni account è durato circa 15-17 secondi. Verdetto: vero positivo, tentativo di persistenza (T1136.001), senza utilizzo successivo visibile negli alert.

## Timeline
Gli orari sono quelli degli alert sul manager. Possono differire da quelli degli eventi anche di decine di secondi ([detections/samples](../detections/samples/README.md)).

**19:28:33, primo account (cmd)**

| Regola | Liv. | Cosa dice | Lettura |
|---|---|---|---|
| 92052 | 4 | cmd avviato da un processo anomalo | rumore, ma apre la sequenza |
| 92036 | 3 | `net.exe` avviato da una shell cmd | prepara il comando successivo |
| 92040 | 12 | `net1.exe` ha eseguito la creazione di un utente | il segnale principale; la riga di comando contiene nome e password in chiaro |
| 60109 (due alert) | 8 | account creato | audit di Security, evento 4720; non ho verificato a quale evento corrisponda il secondo alert |
| 60110 | 8 | account modificato | modifica dell'account appena creato |
| 60170 | 5 | gruppo locale modificato | probabilmente l'ingresso nel gruppo Users (lo deduco, non ho l'evento grezzo) |
| 60160 | 5 | "Domain Users Group Changed" | la descrizione parla di dominio, ma `win-01` non è in un dominio: è rumore di descrizione |

**19:28:48, cancellazione del primo account**

| Regola | Liv. | Cosa dice | Lettura |
|---|---|---|---|
| 92052, 92036 | 4, 3 | stessi processi di prima | comando di pulizia |
| 92039 | 3 | `net.exe` esegue un comando di ricerca account | interroga l'account prima di cancellarlo (lo deduco dall'ordine degli alert) |
| 60170, 60160 | 5 | gruppi modificati | probabilmente l'uscita dai gruppi |
| 60111 | 8 | account disabilitato o eliminato | l'account è vissuto circa 15 secondi |

**19:29:49, secondo account (PowerShell)**

| Regola | Liv. | Cosa dice | Lettura |
|---|---|---|---|
| 92027 | 4 | PowerShell ha avviato un'altra istanza di PowerShell | non dice nulla sull'account |
| 100010 | 3 | file di prova di PowerShell in `%TEMP%` | benigno, è la mia regola di tuning |
| 60109 (due alert), 60110 | 8 | account creato e modificato | solo l'audit di Security: nessun alert sul processo |
| 60160 | 5 | "Domain Users Group Changed" | come sopra |

**19:30:05, cancellazione del secondo account**

| Regola | Liv. | Cosa dice | Lettura |
|---|---|---|---|
| 92027, 100010 | 4, 3 | come prima | comando di pulizia |
| 60160 | 5 | gruppi modificati | |
| 60111 | 8 | account disabilitato o eliminato | il secondo account è vissuto circa 17 secondi |

Nel secondo account manca il 60170: nessuna modifica al gruppo Users. Non ho verificato la causa.

Gli alert tra le 19:21 e le 19:23 (92041, 92302, 92052) sono di un altro test, T1547.001, e non fanno parte di questo incidente: li ho esclusi.

## Domande di triage

| Domanda | Risposta | Fonte |
|---|---|---|
| Chi? | L'utente locale `user` (WIN\user), con integrità High, cioè una sessione da amministratore | [92040](../detections/samples/92040.json), [60109](../detections/samples/60109.json) |
| Cosa è stato creato? | `T1136.001_CMD` con password `T1136.001_CMD!` scritta in chiaro nella riga di comando; poi `T1136.001_PowerShell` | 92040; il secondo nome viene dalla [procedura](procedure.md) |
| Con quale mezzo? | `net user /add` (cmd, poi `net.exe`, poi `net1.exe`); il secondo con il cmdlet `New-LocalUser` | 92036, 92040 |
| Da dove? | Locale: la directory corrente del processo è la cartella Temp dell'utente e negli alert non c'è nessun accesso remoto | 92040 |
| L'account era utilizzabile? | L'evento di creazione riporta UAC 0x0 → 0x15: account disabilitato e "password non richiesta". Un'eventuale abilitazione successiva non è nei miei alert | 60109 |
| C'è persistenza? | Un account locale sopravvive al riavvio e alla chiusura della sessione. Qui è stato cancellato dopo 15-17 secondi, quindi non ha persistito | 60111 |
| È stato usato? | Negli alert della finestra non compare nessun accesso con quei nomi, ma non basta: gli eventi sotto il livello 3 non finiscono in `alerts.json`. Andrebbe cercato l'evento 4624 sul nome dell'account nel log di Security | - |

## Indicatori

| Tipo | Valore | Nota |
|---|---|---|
| Account | `T1136.001_CMD`, `T1136.001_PowerShell` | nomi specifici del test |
| Riga di comando | `net1 user /add "T1136.001_CMD" "T1136.001_CMD!"` | password in chiaro nel log |
| Catena di processi | cmd.exe → net.exe → net1.exe | binari Windows legittimi: non c'è un file malevolo da bloccare, l'indicatore è il comportamento |
| Sequenza | account creato e cancellato in meno di 20 secondi | insolita per un account vero |
| Evento Windows | Security 4720 (account creato) | audit "Gestione account utente" |

## Verdetto
Vero positivo. In un caso reale lo tratterei come ad alta gravità finché non si dimostra che un amministratore l'ha fatto di proposito: la 92040 è a livello 12 e la creazione di un account locale è un passo classico di persistenza.

## Cosa farei per contenerlo
1. Conservare gli alert e i log di `win-01` prima di toccare altro.
2. Chiedere al titolare di `user` se il comando è suo.
3. Se non lo è, isolare la macchina dalla rete (nel lab: sospendere la VM).
4. Disabilitare e cancellare gli account con `net user NOME /active:no` e poi `net user NOME /delete`, se esistono ancora.
5. Cercare accessi con quei nomi (eventi 4624 e 4625).
6. Cambiare le credenziali di `user` e cercare altra persistenza: attività pianificate e chiavi Run, che nel lab coprono le regole 100011, 100012 e 92302.

## Come ha lavorato la detection
Ha funzionato il test 4: due fonti indipendenti, il processo (92040, livello 12) e l'audit di Security (60109), quindi la rilevazione non dipende da una sola. Il livello 12 mi sembra giusto.

Il test 5 è coperto solo dall'audit di Security, a livello 8: se l'audit "Gestione account utente" fosse spento, non ci sarebbe nessun alert. Sul lab è attivo; non l'ho provato spento. Il rumore è alto: 92052, 92036, 92039 e 60160 scattano su qualunque cmd o `net`, e la descrizione della 60160 parla di dominio su un PC senza dominio.

Cosa cambierei:
- Non scriverei una regola nuova per la 92040: funziona.
- Proverei una regola di correlazione sull'account creato e poi cancellato entro un minuto (la 60111 dopo la 60109 sullo stesso nome). Non l'ho scritta.
- Proverei lo Script Block Logging di PowerShell (evento 4104): darebbe un segnale sul comando anche per `New-LocalUser`. Non l'ho provato.

## Limiti di questo report
L'incidente è emulato e io sapevo come finiva. La fonte è una sola, `alerts.json`: ho solo gli eventi che hanno prodotto un alert, non i log grezzi di Sysmon e Security. Non so quale processo abbia avviato il cmd.exe segnalato dalla 92052. Gli orari sono quelli del manager. L'alert grezzo di ogni regola è in [detections/samples](../detections/samples/README.md) e la schermata della 92040 è `evidence/12-T1136.001-default.png`.

Collegati: [docs/README.md](README.md), [procedure.md](procedure.md), [detections/README.md](../detections/README.md).
