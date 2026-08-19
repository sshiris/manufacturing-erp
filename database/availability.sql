\set product_id 
\set order_qty 
with component_availability as (
    select items.name,
bom_item.quantity,
inventory.quantity_on_hand,
inventory.quantity_reserved,
inventory.quantity_on_hand - inventory.quantity_reserved as quantity_available,
bom_item.quantity * :order_qty as quantity_required,
case
    when bom_item.quantity * :order_qty > inventory.quantity_on_hand - inventory.quantity_reserved
         then bom_item.quantity * :order_qty-(inventory.quantity_on_hand - inventory.quantity_reserved)
    else 0
end as quantity_shortage
from bom_item
join items
on bom_item.component_id = items.id
join inventory 
on bom_item.component_id = inventory.item_id
where bom_item.parent_id = :product_id
)

select sum(quantity_shortage) as total_shortage,
case
when sum(quantity_shortage) > 0 then false
else true
end as can_fulfill
from component_availability;