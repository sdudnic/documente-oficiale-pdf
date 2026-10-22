# Stil și verificare

## Aspect

Aspectul implicit reproduce un document oficial sobru: corp serif justificat, spațiere reală între blocuri, titluri îngroșate, copertă aerisită, anexă pe pagină nouă și referințe pe două coloane. Nu adăuga chenare, linii orizontale, culori decorative sau antete încărcate.

## Verificări

După generare, verifică cel puțin:

1. toate paginile conțin text;
2. nu apar caractere de înlocuire (`�`), URL-uri deformate sau spații duble accidentale;
3. numărul legăturilor active din PDF acoperă toate URL-urile din Markdown;
4. prima pagină conține destinatarul și titlul, iar anexa începe după separator;
5. titlurile și blocurile de identificare nu sunt tăiate la marginea paginii;
6. pagina de referințe nu revarsă text în afara celor două coloane.

Pentru o verificare vizuală, randează PDF-ul cu Poppler sau cu instrumentul PDF al mediului și inspectează cel puțin coperta, pagina de tranziție către anexă și paginile de referințe. Raportul JSON produs de script este util pentru verificarea automată, dar nu înlocuiește inspecția vizuală atunci când documentul urmează să fie transmis oficial.
