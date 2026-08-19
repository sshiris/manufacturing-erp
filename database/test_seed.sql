truncate table bom_item, inventory, items restart identity;
insert into items(name)
values
    ('DESK'),
    ('CHAIR'),
    ('LEG'),
    ('TABLETOP'),
    ('SCREW')
;

insert into bom_item(parent_id, component_id, quantity)
values(
    (select id from items where name = 'DESK'),
    (select id from items where name = 'LEG'),
    4
),
(
    (select id from items where name = 'DESK'),
    (select id from items where name = 'TABLETOP'),
    1
),
(
    (select id from items where name = 'DESK'),
    (select id from items where name = 'SCREW'),
    8
)
;

insert into inventory(
    item_id,
    quantity_on_hand,
    quantity_reserved
)
values
    ((select id from items where name = 'LEG'),
    50,
    10),
    ((select id from items where name = 'TABLETOP'),
    6,
    0),
    ((select id from items where name = 'SCREW'),
    500,
    100)
;