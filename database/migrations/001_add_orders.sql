create table orders (
    id int generated always as identity primary key,
    product_id int not null references items(id),
    quantity numeric(12,3) not null check (quantity > 0),
    unit_price numeric(12,2) not null check (unit_price >= 0),
    status varchar(80) not null default 'pending' 
        check (status in ('pending', 'reserved', 'in_progress', 'completed')),
    created_at timestamp not null default current_timestamp,
    estimated_delivery_date timestamp
);