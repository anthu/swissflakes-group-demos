{{ config(materialized='semantic_view') }}

TABLES (
  r AS {{ ref('revenue_by_route') }}
    WITH SYNONYMS = ('routes', 'revenue', 'Umsatz', 'Strecken')
    COMMENT = 'Revenue and delivery metrics aggregated by shipping route'
)
FACTS (
  r.total_shipments AS r.TOTAL_SHIPMENTS WITH SYNONYMS = ('shipment count', 'Anzahl Sendungen') COMMENT = 'Total shipments on this route',
  r.total_orders AS r.TOTAL_ORDERS WITH SYNONYMS = ('order count', 'Anzahl Bestellungen') COMMENT = 'Total orders on this route',
  r.total_revenue_chf AS r.TOTAL_REVENUE_CHF WITH SYNONYMS = ('gross revenue', 'Bruttoumsatz') COMMENT = 'Total gross revenue in CHF',
  r.total_payments_chf AS r.TOTAL_PAYMENTS_CHF WITH SYNONYMS = ('payment volume', 'Zahlungsvolumen') COMMENT = 'Total payment volume in CHF',
  r.total_refunds_chf AS r.TOTAL_REFUNDS_CHF WITH SYNONYMS = ('refund volume', 'Rueckerstattungen') COMMENT = 'Total refund amount in CHF',
  r.net_revenue_chf AS r.NET_REVENUE_CHF WITH SYNONYMS = ('net income', 'Nettoumsatz') COMMENT = 'Net revenue after refunds in CHF',
  r.avg_delivery_days AS r.AVG_DELIVERY_DAYS WITH SYNONYMS = ('average delivery time', 'durchschnittliche Lieferzeit') COMMENT = 'Average delivery days on this route',
  r.avg_order_value_chf AS r.AVG_ORDER_VALUE_CHF WITH SYNONYMS = ('average order size', 'durchschnittlicher Bestellwert') COMMENT = 'Average order value in CHF'
)
DIMENSIONS (
  r.origin_warehouse AS r.ORIGIN_WAREHOUSE WITH SYNONYMS = ('warehouse', 'origin', 'Lager', 'Abgangsort') COMMENT = 'Origin warehouse for shipments',
  r.destination_city AS r.DESTINATION_CITY WITH SYNONYMS = ('delivery city', 'destination', 'Zielort', 'Lieferstadt') COMMENT = 'Destination city for shipments'
)
METRICS (
  r.total_net_revenue AS SUM(r.net_revenue_chf) WITH SYNONYMS = ('overall net revenue', 'Gesamtnettoumsatz') COMMENT = 'Total net revenue across all routes',
  r.total_route_shipments AS SUM(r.total_shipments) WITH SYNONYMS = ('overall shipments', 'Gesamtsendungen') COMMENT = 'Total shipments across all routes',
  r.avg_route_delivery_days AS AVG(r.avg_delivery_days) WITH SYNONYMS = ('overall avg delivery time', 'Gesamtlieferzeit') COMMENT = 'Average delivery time across all routes'
)
COMMENT = 'Revenue analytics by shipping route for SwissFlakes Logistics'
