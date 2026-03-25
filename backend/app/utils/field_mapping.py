"""
Field Mapping Configuration
============================
Centralizes all SAP JSON field name mappings.
If your actual JSON files use different field names, adjust here.

This is the single place to update if ingestion fails due to field mismatches.
"""

# ---- Business Partners ----
BP_FIELDS = {
    "customer_id": ["BusinessPartner", "business_partner", "Customer", "customer_id"],
    "name": ["BusinessPartnerFullName", "BusinessPartnerName", "name", "FullName"],
    "country": ["Country", "CountryRegion", "country"],
    "city": ["CityName", "city"],
    "region": ["Region", "region"],
}

# ---- Business Partner Addresses ----
ADDR_FIELDS = {
    "address_id": ["AddressID", "address_id", "BusinessPartnerAddressID"],
    "customer_id": ["BusinessPartner", "business_partner", "Customer"],
    "street": ["StreetName", "Street", "street"],
    "city": ["CityName", "city"],
    "postal_code": ["PostalCode", "postal_code"],
    "country": ["Country", "country"],
}

# ---- Plants ----
PLANT_FIELDS = {
    "plant_id": ["Plant", "plant", "plant_id"],
    "name": ["PlantName", "name"],
    "country": ["Country", "country"],
    "city": ["CityName", "city"],
}

# ---- Products ----
PRODUCT_FIELDS = {
    "product_id": ["Product", "product", "Material", "material", "product_id"],
    "description": ["ProductDescription", "Description", "description"],
    "product_group": ["ProductGroup", "product_group"],
    "base_unit": ["BaseUnit", "BaseUnitOfMeasure", "base_unit"],
}

# ---- Sales Order Headers ----
SO_FIELDS = {
    "order_id": ["SalesOrder", "sales_order", "order_id", "OrderID"],
    "customer_id": ["SoldToParty", "Customer", "customer_id", "BusinessPartner"],
    "order_date": ["SalesOrderDate", "CreationDate", "order_date"],
    "net_value": ["TotalNetAmount", "NetAmount", "NetValue", "net_value"],
    "currency": ["TransactionCurrency", "Currency", "currency"],
    "status": ["SalesOrderProcessingStatus", "OverallStatus", "status"],
    "sales_org": ["SalesOrganization", "SalesOrg", "sales_org"],
}

# ---- Sales Order Items ----
SOI_FIELDS = {
    "item_id": ["SalesOrderItem", "item_id"],
    "order_id": ["SalesOrder", "sales_order", "order_id"],
    "product_id": ["Material", "Product", "product_id"],
    "quantity": ["OrderQuantity", "Quantity", "quantity"],
    "net_value": ["NetAmount", "NetValue", "net_value"],
    "currency": ["TransactionCurrency", "Currency", "currency"],
}

# ---- Schedule Lines ----
SL_FIELDS = {
    "order_id": ["SalesOrder", "sales_order"],
    "item_id": ["SalesOrderItem", "item_id"],
    "confirmed_qty": ["ConfdOrderQtyByMatlAvailCheck", "ConfirmedQuantity", "confirmed_qty"],
    "delivery_date": ["ScheduleLineDeliveryDate", "DeliveryDate", "delivery_date"],
}

# ---- Delivery Headers ----
DLV_FIELDS = {
    "delivery_id": ["DeliveryDocument", "delivery_id", "OutboundDelivery"],
    "order_id": ["SalesOrder", "sales_order", "ReferenceSDDocument", "order_id"],
    "plant_id": ["ShippingPoint", "Plant", "plant_id"],
    "delivery_date": ["PlannedGoodsIssueDate", "DeliveryDate", "delivery_date"],
    "actual_goods_movement_date": ["ActualGoodsMovementDate", "actual_goods_movement_date"],
    "status": ["OverallSDProcessStatus", "DeliveryStatus", "status"],
}

# ---- Delivery Items ----
DLVI_FIELDS = {
    "item_id": ["DeliveryDocumentItem", "item_id"],
    "delivery_id": ["DeliveryDocument", "delivery_id"],
    "product_id": ["Material", "Product", "product_id"],
    "order_id": ["ReferenceSDDocument", "SalesOrder", "order_id"],
    "quantity": ["ActualDeliveryQuantity", "DeliveryQuantity", "quantity"],
}

# ---- Billing Document Headers ----
BIL_FIELDS = {
    "billing_id": ["BillingDocument", "billing_id"],
    "order_id": ["SalesOrder", "ReferenceSDDocument", "order_id"],
    "delivery_id": ["DeliveryDocument", "ReferenceDocument", "delivery_id"],
    "customer_id": ["PayerParty", "SoldToParty", "Customer", "customer_id"],
    "billing_date": ["BillingDocumentDate", "CreationDate", "billing_date"],
    "net_value": ["TotalNetAmount", "NetAmount", "NetValue", "net_value"],
    "currency": ["TransactionCurrency", "Currency", "currency"],
    "status": ["BillingDocumentProcessingStatus", "OverallStatus", "status"],
}

# ---- Billing Items ----
BILI_FIELDS = {
    "item_id": ["BillingDocumentItem", "item_id"],
    "billing_id": ["BillingDocument", "billing_id"],
    "product_id": ["Material", "Product", "product_id"],
    "quantity": ["BillingQuantity", "Quantity", "quantity"],
    "net_value": ["NetAmount", "NetValue", "net_value"],
    "currency": ["TransactionCurrency", "Currency", "currency"],
}

# ---- Billing Cancellations ----
BILC_FIELDS = {
    "cancellation_id": ["BillingDocument", "CancellationBillingDocument", "cancellation_id"],
    "original_billing_id": ["CancelledBillingDocument", "OriginalBillingDocument", "original_billing_id"],
    "cancel_date": ["BillingDocumentDate", "CancellationDate", "cancel_date"],
    "reason": ["BillingDocumentCategory", "CancellationReason", "reason"],
}

# ---- Journal Entry Items (AR) ----
JE_FIELDS = {
    "entry_id": ["AccountingDocument", "entry_id", "JournalEntryID"],
    "billing_id": ["BillingDocument", "ReferenceDocument", "billing_id"],
    "customer_id": ["Customer", "CustomerID", "customer_id"],
    "posting_date": ["PostingDate", "posting_date"],
    "amount": ["AmountInTransactionCurrency", "Amount", "amount"],
    "currency": ["TransactionCurrency", "Currency", "currency"],
    "account": ["GLAccount", "Account", "account"],
}

# ---- Payments (AR) ----
PAY_FIELDS = {
    "payment_id": ["PaymentDocument", "ClearingDocument", "payment_id"],
    "customer_id": ["Customer", "customer_id"],
    "billing_id": ["BillingDocument", "AssignmentReference", "billing_id"],
    "journal_entry_id": ["AccountingDocument", "ClearingAccountingDocument", "journal_entry_id"],
    "payment_date": ["PostingDate", "ClearingDate", "payment_date"],
    "amount": ["AmountInTransactionCurrency", "Amount", "amount"],
    "currency": ["TransactionCurrency", "Currency", "currency"],
}


def pick(record: dict, candidates: list, default=None):
    """
    Try each candidate field name in order and return the first match.
    Handles both exact and case-insensitive lookups.
    """
    for key in candidates:
        if key in record and record[key] not in (None, "", "00000000"):
            return record[key]
    # Case-insensitive fallback
    lower_record = {k.lower(): v for k, v in record.items()}
    for key in candidates:
        if key.lower() in lower_record and lower_record[key.lower()] not in (None, "", "00000000"):
            return lower_record[key.lower()]
    return default


def safe_float(val, default=0.0):
    try:
        return float(val) if val else default
    except (ValueError, TypeError):
        return default
