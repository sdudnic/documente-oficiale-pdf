# documente-oficiale-pdf

Skill Codex reutilizabil pentru formatarea petițiilor, demersurilor, sesizărilor, memoriilor și anexelor juridice în PDF oficial A4.

Mise en page-ul include adresare aerisită, font serif de tip Times, titluri clare, anexă separată, subsol cu paginare, legături active și referințe compacte pe două coloane. Formatul este independent de limbă, instituție și obiect; skillul nu modifică fondul juridic și nu verifică temeinicia afirmațiilor.

## Instalare

Clonează depozitul în directorul de skilluri al instanței Codex:

```powershell
git clone https://github.com/sdudnic/documente-oficiale-pdf.git `
  "$env:CODEX_HOME\skills\documente-oficiale-pdf"
```

Dacă variabila `CODEX_HOME` nu este configurată, folosește directorul local de skilluri al instalării Codex.

## Utilizare

Păstrează documentul sursă ca Markdown UTF-8 și rulează din directorul skillului:

```powershell
python ".\scripts\format_pdf.py" `
  --source "D:\proiect\document.md" `
  --output "D:\proiect\output\document.pdf" `
  --footer "Denumirea documentului" `
  --pdf-title "Denumirea documentului" `
  --report "D:\proiect\output\document.json"
```

Sunt necesare Python 3 și bibliotecile `reportlab` și `pypdf`:

```powershell
python -m pip install reportlab pypdf
```

Regulile complete de structură și verificare se află în `SKILL.md` și în directorul `references/`.
