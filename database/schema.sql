CREATE TABLE items (
    id int generated always as identity primary key,
    name varchar(255) not null,
    status varchar(80) default 'active'
);
CREATE TABLE bom_item(
    parent_id int references items(id),
    component_id int references items(id),
    quantity numeric(12,3) not null check (quantity > 0),
    primary key(parent_id, component_id),
    check (parent_id != component_id)
);
create table inventory (
    item_id int references items(id) primary key,
    quantity_on_hand numeric(12,3) not null default 0 check (quantity_on_hand >=0),
    quantity_reserved numeric(12,3) not null default 0 check (quantity_reserved >=0),
    check (quantity_reserved <= quantity_on_hand)
)

with component_availability as (
    select items.name,
bom_item.quantity,
inventory.quantity_on_hand,
inventory.quantity_reserved,
inventory.quantity_on_hand - inventory.quantity_reserved as quantity_available,
bom_item.quantity * 10 as quantity_required,
case
    when bom_item.quantity * 10 > inventory.quantity_on_hand - inventory.quantity_reserved
         then bom_item.quantity * 10-(inventory.quantity_on_hand - inventory.quantity_reserved)
    else 0
end as quantity_shortage
from bom_item
join items
on bom_item.component_id = items.id
join inventory 
on bom_item.component_id = inventory.item_id
where bom_item.parent_id = 1
)

select sum(quantity_shortage) as total_shortage,
case
    when sum(quantity_shortage) > 0 then false
    else true
end as can_fulfill
from component_availability;