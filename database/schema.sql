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