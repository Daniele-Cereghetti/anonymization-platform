# Ground Truth Annotations

Manual annotations of sensitive entities for documents `01`–`04` of the dataset, used to compute precision/recall/F1 against the system's predictions.

## File format

One JSON file per dataset document. Filename mirrors the document name (e.g. `01_CV_IT.json` for `01_CV_IT.md`).

```json
{
  "document": "01_CV_IT.md",
  "entities": [
    {"value": "Marta Bianchi", "category": "persone_fisiche", "entity_type": "nome_cognome"},
    ...
  ]
}
```

`category` ∈ {`persone_fisiche`, `persone_giuridiche`, `dati_contatto`, `identificativi`, `dati_finanziari`, `dati_temporali`}.

## Annotation policy

- `value` is the exact string as it appears in the source `.md` (matching is case-insensitive and whitespace-tolerant in the evaluator).
- Each unique `(value, category)` is listed once per document, even if the string appears multiple times.
- Included: full names, organization names, full addresses, phone numbers, emails, IBANs, tax codes (CF/SSN/AVS), ID document numbers, license plates, license/credential IDs, LinkedIn URLs, signature/contract IDs, POD/PDR codes, dates of birth, document issuance dates, contract validity periods.
- Excluded: monetary amounts, percentages, generic years of experience, generic working periods (e.g. "2021–present"), generic job titles, certifications without IDs, city names appearing standalone (kept only when part of a full address).
