# Sysmon vedeva ogni attività pianificata, Wazuh non ne segnalava nessuna (T1053.005)

## Sintomo
Ho eseguito i test Atomic Red Team T1053.005-2, -4 e -6, che creano un'attività pianificata con tre metodi diversi: `schtasks.exe`, cmdlet PowerShell e WMI. Nella dashboard compaiono solo regole generiche (92004, 92052, 92032, 92027 e 100010). Nessun alert nomina un'attività pianificata (`evidence/09-T1053.005-default-none.png`).

## Diagnosi
Prima ho verificato se il problema fosse la telemetria. Con `Get-WinEvent` su Sysmon, in locale, trovo gli eventi per tutti e tre i metodi:
- test 2: EID 1 `schtasks.exe /Create ...` ed EID 11 `C:\Windows\System32\Tasks\spawn`;
- test 4: EID 1 `powershell.exe` con `New-ScheduledTaskAction` ed EID 11 `...\Tasks\AtomicTask`;
- test 6: EID 1 `powershell.exe` ed EID 11 `...\Tasks\T1053_005_WMI`.

La telemetria c'è, quindi il buco è nelle regole: nessuna regola di default interpreta questi eventi. Non posso nemmeno ripiegare sul registro, perché la configurazione Sysmon che uso non registra le chiavi `TaskCache` (EID 12 e 13). L'unico segnale in comune ai tre metodi è la creazione del file di definizione in `C:\Windows\System32\Tasks\`.

## Soluzione
Ho scritto due regole in `detections/local_rules.xml`:
- 100011 (livello 8): Sysmon EID 11 con file in `System32\Tasks`, qualunque sia il metodo. Ho scelto livello 8 e non più alto perché anche software legittimo crea attività pianificate.
- 100012 (livello 10): `schtasks.exe` con `/create` nella riga di comando. Qui il comando è inequivocabile, per questo il livello è più alto.

Ho rieseguito i tre test con la pulizia finale. Il test 2 genera la 100012 e la 100011; i test 4 e 6 generano la 100011 (`evidence/10-T1053.005-custom-rule.png`). Le pulizie non producono alert.

## Lezione
Avere i log non vuol dire rilevare: Sysmon registrava tutto, ma senza una regola nessuno lo vedeva. Per una tecnica con più metodi mi aggancio al risultato comune, cioè il file di definizione, e non al singolo comando.

Due limiti. Nei test 4 e 6 la riga di comando dei cmdlet è visibile solo perché Atomic Red Team avvia un `powershell.exe` figlio; un attaccante già dentro una sessione aperta non lo produrrebbe e l'unico segnale resterebbe la 100011. Inoltre ho osservato i falsi positivi della 100011 solo per pochi minuti, quindi vanno misurati su più giorni. Il segnale sul registro (`TaskCache`) non lo uso perché la configurazione Sysmon non lo registra: provarne una che lo registri e confrontarla con la 100011 è un confronto che non ho ancora fatto.

Collegati: [writeups/README.md](README.md), [detections/README.md](../detections/README.md), [docs/procedure.md](../docs/procedure.md).
