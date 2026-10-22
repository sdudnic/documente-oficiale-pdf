---
name: documente-oficiale-pdf
description: Formatează petiții, demersuri, sesizări, memorii și anexe juridice în PDF oficial A4, cu aspect sobru, paginare, linkuri active și referințe pe două coloane.
---

# Documente oficiale PDF

Folosește acest skill pentru orice adresare juridică, demers, petiție, sesizare, memoriu sau anexă care trebuie să aibă acest aspect oficial: pagină A4, font serif de tip Times, adresare aerisită, titluri clare, anexă separată, subsol cu numele documentului și referințe compacte pe două coloane. Formatul este independent de limbă, instituție și obiect. Skillul se ocupă de punerea în pagină și de verificarea tehnică; nu inventa sau modifica fondul juridic, faptele ori sursele.

## Fluxul de lucru

1. Păstrează textul într-un fișier Markdown UTF-8. Folosește paragrafe separate prin linii goale, `#`/`##`/`###` pentru titluri, liste numerotate pentru cereri și legături Markdown pentru surse.
2. Pentru copertă, pune mai întâi blocul destinatarului, apoi blocul expeditorului (dacă există), apoi linia `**Obiect: ...**`, `**Subiect: ...**` sau echivalentul în limba documentului. Un separator `---` marchează trecerea la partea principală ori la anexă.
3. Pentru o anexă, un titlu de nivel 1 care începe cu `# Proiect`, `# Project` sau echivalentul în limba documentului este afișat ca anexă separată, cu eticheta implicită `ANEXĂ`. Un bloc de identificare cu câmpuri de forma `Etichetă: valoare` poate fi transformat într-un tabel discret cu două coloane.
4. Un titlu de referințe precum `## Surse și repere`, `## Referințe`, `## Sources` sau `## Источники и ориентиры` începe pe pagină nouă și trece într-un cadru cu două coloane. Legăturile Markdown trebuie să rămână active în PDF.
5. Rulează `scripts/format_pdf.py` din acest skill. Dacă lucrezi într-un alt proiect, copiază scriptul în proiect sau apelează-l cu calea absolută.
6. Verifică PDF-ul prin extragere de text și prin randarea paginilor când aspectul contează. Nu livra un PDF dacă există pagini goale, caractere de înlocuire, text tăiat sau legături lipsă.

## Stilul implicit

- A4; margini stânga/dreapta 25 mm, sus 22 mm, jos 24 mm.
- Font serif compatibil Times New Roman; pe Windows se folosesc fonturile Times locale, iar scriptul caută automat un fallback serif dacă acestea lipsesc.
- Corp: aproximativ 10,8 pt, interlinie 14,5 pt, aliniere justificată.
- Titluri de secțiune îngroșate, cu spațiu înainte și după; nu folosi linii decorative sau separatoare vizibile în interiorul documentului.
- Footer discret, cu denumirea scurtă la stânga și `pagina / total` la dreapta.
- Referințe: aproximativ 8,4 pt, interlinie 10,1 pt, în două coloane, cu păstrarea legăturilor active.
- Nu pune URL-uri brute în titluri sau antete dacă utilizatorul nu le cere; leagă sursa prin titlul ei.

## Comandă

```powershell
python ".\scripts\format_pdf.py" `
  --source "D:\proiect\document.md" `
  --output "D:\proiect\output\document.pdf" `
  --footer "Denumirea documentului" `
  --pdf-title "Denumirea documentului"
```

Rulează comanda din directorul skillului sau înlocuiește `.\scripts\format_pdf.py` cu calea locală a fișierului `scripts/format_pdf.py`.

Parametrii opționali `--cover-label`, `--annex-label` și `--references-heading` permit adaptarea aceleiași mise en page la orice limbă sau tip de document. Dacă `--references-heading` nu este indicat, scriptul încearcă să recunoască titlurile uzuale în moldovenească, rusă, engleză și franceză. Scriptul creează și un raport JSON lângă PDF dacă se indică `--report`.

Pentru regulile Markdown și exemplele de structură, citește [references/structura-markdown.md](references/structura-markdown.md). Pentru detaliile vizuale și verificările obligatorii, citește [references/stil-si-verificare.md](references/stil-si-verificare.md).
