# Structura Markdown acceptată

Scriptul este intenționat simplu și păstrează textul utilizatorului. Forma recomandată este:

```markdown
Destinatarul
Adresa destinatarului

De la:
____________________________
Adresa de corespondență:
____________________________

**Obiect: examinarea unei sesizări**

Stimate ...,

Textul demersului.

1. Prima cerere.
2. A doua cerere.

---

# Proiect de demers privind ...

Destinatarul anexei
Adresa

Autorul sesizării: ...
Adresa de corespondență: ...
IDNO: ...

Abrevieri: ...

## 1 Obiectul

Textul juridic.

### 1.1 Subsecțiune

Textul subsecțiunii.

## Surse și repere

**[S1] Constituția**

Constituția Republicii Moldova — [sursa](https://example.org/document.pdf).
```

Reguli:

- Liniile goale separă blocurile care trebuie să rămână distincte vizual.
- `#`, `##` și `###` sunt folosite numai pentru titluri; nu simula titlurile cu majuscule în corp.
- Listele numerotate se pun câte un element pe linie. Pentru o cerere juridică, folosește verbe la infinitiv sau formularea pe care o cere utilizatorul.
- Folosește `[titlul sursei](URL)` pentru legături active. Nu duplica aceeași sursă printr-un URL brut separat.
- Titlul secțiunii de referințe poate fi indicat prin `--references-heading`; în lipsa lui, scriptul recunoaște titluri uzuale în mai multe limbi.
- Nu include în document instrucțiuni editoriale de tipul „de completat”, „se completează” sau explicații despre pașii interni, decât dacă utilizatorul le cere.
