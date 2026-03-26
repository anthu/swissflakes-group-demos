{{ config(materialized='semantic_view') }}

TABLES (
  fl AS {{ ref('fulfillment_lifecycle') }}
    PRIMARY KEY (ORDER_ID)
    WITH SYNONYMS = ('fulfillment', 'orders', 'deliveries', 'Auftragsabwicklung')
    COMMENT = 'Full order-to-delivery lifecycle joining orders, shipments, and payments'
)
FACTS (
  fl.order_total_chf AS fl.ORDER_TOTAL_CHF WITH SYNONYMS = ('order amount', 'order value', 'Bestellwert') COMMENT = 'Total value of the order in Swiss Francs',
  fl.delivery_days AS fl.DELIVERY_DAYS WITH SYNONYMS = ('delivery time', 'transit time', 'Lieferzeit') COMMENT = 'Number of days between shipment dispatch and delivery',
  fl.payment_amount_chf AS fl.PAYMENT_AMOUNT_CHF WITH SYNONYMS = ('payment total', 'Zahlungsbetrag') COMMENT = 'Gross payment amount in Swiss Francs',
  fl.net_payment_chf AS fl.NET_PAYMENT_CHF WITH SYNONYMS = ('net amount', 'Nettobetrag') COMMENT = 'Net payment amount after fees and deductions'
)
DIMENSIONS (
  fl.order_id AS fl.ORDER_ID WITH SYNONYMS = ('order number', 'Bestellnummer') COMMENT = 'Unique order identifier',
  fl.customer_id AS fl.CUSTOMER_ID WITH SYNONYMS = ('customer number', 'Kundennummer') COMMENT = 'Customer identifier',
  fl.order_status AS fl.ORDER_STATUS WITH SYNONYMS = ('order state', 'Bestellstatus') COMMENT = 'Order status: PENDING, SHIPPED, DELIVERED, CANCELLED',
  fl.shipment_id AS fl.SHIPMENT_ID WITH SYNONYMS = ('shipment number', 'Sendungsnummer') COMMENT = 'Shipment identifier',
  fl.shipment_status AS fl.SHIPMENT_STATUS WITH SYNONYMS = ('shipment state', 'Versandstatus') COMMENT = 'Shipment status: IN_TRANSIT, DELIVERED, RETURNED',
  fl.vehicle_id AS fl.VEHICLE_ID WITH SYNONYMS = ('truck id', 'Fahrzeug-ID') COMMENT = 'Delivery vehicle identifier',
  fl.origin_warehouse AS fl.ORIGIN_WAREHOUSE WITH SYNONYMS = ('warehouse', 'origin', 'Lager', 'Abgangsort') COMMENT = 'Warehouse where the shipment originates',
  fl.destination_city AS fl.DESTINATION_CITY WITH SYNONYMS = ('delivery city', 'destination', 'Zielort', 'Lieferstadt') COMMENT = 'Delivery destination city',
  fl.payment_id AS fl.PAYMENT_ID WITH SYNONYMS = ('payment number', 'Zahlungs-ID') COMMENT = 'Payment transaction identifier',
  fl.payment_method AS fl.PAYMENT_METHOD WITH SYNONYMS = ('payment type', 'Zahlungsart') COMMENT = 'Payment method: CREDIT_CARD, BANK_TRANSFER, TWINT',
  fl.payment_status AS fl.PAYMENT_STATUS WITH SYNONYMS = ('payment state', 'Zahlungsstatus') COMMENT = 'Payment status: COMPLETED, PENDING, REFUNDED',
  fl.order_date AS fl.ORDER_DATE WITH SYNONYMS = ('order placed date', 'Bestelldatum') COMMENT = 'Date when the order was placed',
  fl.shipped_at AS fl.SHIPPED_AT WITH SYNONYMS = ('ship date', 'dispatch date', 'Versanddatum') COMMENT = 'Timestamp when the shipment was dispatched',
  fl.delivered_at AS fl.DELIVERED_AT WITH SYNONYMS = ('delivery date', 'Lieferdatum') COMMENT = 'Timestamp when the shipment was delivered'
)
METRICS (
  fl.total_revenue AS SUM(fl.order_total_chf) WITH SYNONYMS = ('revenue', 'Gesamtumsatz') COMMENT = 'Total revenue from all orders in CHF',
  fl.avg_delivery_days AS AVG(fl.delivery_days) WITH SYNONYMS = ('average delivery time', 'durchschnittliche Lieferzeit') COMMENT = 'Average delivery days across shipments',
  fl.total_payments AS SUM(fl.payment_amount_chf) WITH SYNONYMS = ('payment volume', 'Zahlungsvolumen') COMMENT = 'Total gross payment amount in CHF',
  fl.order_count AS COUNT(DISTINCT fl.order_id) WITH SYNONYMS = ('number of orders', 'Anzahl Bestellungen') COMMENT = 'Total number of unique orders',
  fl.shipment_count AS COUNT(DISTINCT fl.shipment_id) WITH SYNONYMS = ('number of shipments', 'Anzahl Sendungen') COMMENT = 'Total number of unique shipments'
)
COMMENT = 'Fulfillment analytics: order-to-delivery lifecycle for SwissFlakes Logistics'
