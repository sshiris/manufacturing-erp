def calculate_availability(
    bom_quantity,
    quantity_on_hand,
    quantity_reserved,
    order_qty
):
    quantity_required = bom_quantity * order_qty
    quantity_available = quantity_on_hand - quantity_reserved
    quantity_shortage = max(0, quantity_required - quantity_available)
    
    return {
        "quantity_required": quantity_required,
        "quantity_available": quantity_available,
        "quantity_shortage": quantity_shortage
    }