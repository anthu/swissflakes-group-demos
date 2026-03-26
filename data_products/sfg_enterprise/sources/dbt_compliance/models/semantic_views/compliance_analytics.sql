{{ config(materialized='semantic_view') }}

TABLES (
  t AS {{ ref('transaction_report') }}
    PRIMARY KEY (PAYMENT_ID)
    WITH SYNONYMS = ('transactions', 'compliance', 'FINMA', 'BAZG', 'GwG', 'Transaktionen')
    COMMENT = 'Compliance transaction report for FINMA, BAZG, and GwG regulations'
)
FACTS (
  t.amount_chf AS t.AMOUNT_CHF WITH SYNONYMS = ('transaction amount', 'Betrag', 'Transaktionsbetrag') COMMENT = 'Transaction amount in Swiss Francs'
)
DIMENSIONS (
  t.payment_id AS t.PAYMENT_ID WITH SYNONYMS = ('transaction id', 'Zahlungs-ID') COMMENT = 'Unique payment transaction identifier',
  t.order_id AS t.ORDER_ID WITH SYNONYMS = ('order number', 'Bestellnummer') COMMENT = 'Associated order identifier',
  t.customer_id AS t.CUSTOMER_ID WITH SYNONYMS = ('customer number', 'Kundennummer') COMMENT = 'Customer identifier',
  t.company_name AS t.COMPANY_NAME WITH SYNONYMS = ('firm', 'business name', 'Firmenname') COMMENT = 'Company name associated with the transaction',
  t.payment_method AS t.PAYMENT_METHOD WITH SYNONYMS = ('payment type', 'Zahlungsart') COMMENT = 'Payment method: CREDIT_CARD, BANK_TRANSFER, TWINT',
  t.payment_status AS t.PAYMENT_STATUS WITH SYNONYMS = ('payment state', 'Zahlungsstatus') COMMENT = 'Payment status: COMPLETED, PENDING, REFUNDED',
  t.is_international AS t.IS_INTERNATIONAL WITH SYNONYMS = ('cross-border', 'grenzueberschreitend') COMMENT = 'Whether the transaction involves international parties',
  t.requires_aml_check AS t.REQUIRES_AML_CHECK WITH SYNONYMS = ('AML flag', 'GwG check', 'Geldwaeschereiproofung') COMMENT = 'Flagged for Anti-Money Laundering review under GwG',
  t.shipment_id AS t.SHIPMENT_ID WITH SYNONYMS = ('shipment number', 'Sendungsnummer') COMMENT = 'Associated shipment identifier',
  t.requires_customs AS t.REQUIRES_CUSTOMS WITH SYNONYMS = ('customs flag', 'BAZG flag', 'Zollpflichtig') COMMENT = 'Requires BAZG customs declaration',
  t.customs_declaration_id AS t.CUSTOMS_DECLARATION_ID WITH SYNONYMS = ('customs number', 'Zolldeklarationsnummer', 'BAZG reference') COMMENT = 'BAZG customs declaration reference number',
  t.created_at AS t.CREATED_AT WITH SYNONYMS = ('creation date', 'Erstelldatum') COMMENT = 'Date when the transaction was created',
  t.processed_at AS t.PROCESSED_AT WITH SYNONYMS = ('processing date', 'Verarbeitungsdatum') COMMENT = 'Date when the transaction was processed'
)
METRICS (
  t.total_amount AS SUM(t.amount_chf) WITH SYNONYMS = ('total volume', 'Gesamtbetrag') COMMENT = 'Total transaction amount in CHF',
  t.transaction_count AS COUNT(t.payment_id) WITH SYNONYMS = ('number of transactions', 'Anzahl Transaktionen') COMMENT = 'Total number of transactions',
  t.aml_flagged_count AS COUNT_IF(t.requires_aml_check = TRUE) WITH SYNONYMS = ('AML count', 'GwG flagged') COMMENT = 'Transactions flagged for AML review',
  t.customs_required_count AS COUNT_IF(t.requires_customs = TRUE) WITH SYNONYMS = ('customs count', 'Zollpflichtige Transaktionen') COMMENT = 'Transactions requiring customs declarations',
  t.international_count AS COUNT_IF(t.is_international = TRUE) WITH SYNONYMS = ('cross-border count', 'internationale Transaktionen') COMMENT = 'International cross-border transactions'
)
COMMENT = 'Compliance analytics for FINMA, BAZG customs, and GwG AML reporting'
