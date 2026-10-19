from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from decimal import Decimal

from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size, SizeChart
from app.models.commerce import Inventory
from app.models.user import Role, User, user_roles


def seed_database(session: Session) -> None:
    if session.scalar(select(User.id).limit(1)) is None:
        session.add(
            User(
                email="demo@example.com",
                password_hash=hash_password("Demo-123!"),
                display_name="演示用户",
            )
        )
    if session.scalar(select(User.id).where(User.email == "admin@example.com")) is None:
        session.add(User(email="admin@example.com", password_hash=hash_password("Admin-123!"), display_name="运营管理员"))
    existing_roles = {name for name in session.scalars(select(Role.name)).all()}
    for name in ("customer", "operator", "admin", "super_admin"):
        if name not in existing_roles:
            session.add(Role(name=name))
    session.flush()
    admin = session.scalar(select(User).where(User.email == "admin@example.com"))
    admin_role = session.scalar(select(Role).where(Role.name == "admin"))
    if admin is not None and admin_role is not None and session.scalar(select(user_roles.c.user_id).where(user_roles.c.user_id == admin.id, user_roles.c.role_id == admin_role.id)) is None:
        session.execute(user_roles.insert().values(user_id=admin.id, role_id=admin_role.id))
    category = session.scalar(select(ProductCategory).where(ProductCategory.slug == "tops"))
    if category is None:
        category = ProductCategory(name="上衣", slug="tops")
        session.add(category)
        session.flush()
    if session.scalar(select(Product.id).limit(1)) is None:
        colors = [Color(name="曜石黑", hex_value="#161616"), Color(name="云雾白", hex_value="#F3F1EC")]
        sizes = [Size(name="S", sort_order=1), Size(name="M", sort_order=2), Size(name="L", sort_order=3)]
        session.add_all(colors + sizes)
        session.flush()
        products = [
            Product(
                category_id=category.id,
                name="轻盈防风风衣",
                slug="light-trench-coat",
                description="轻盈防风，适合春秋通勤与城市出行。",
                fabric_info="聚酯纤维混纺",
                care_instructions="建议冷水轻柔洗涤",
                status="published",
            ),
            Product(
                category_id=category.id,
                name="云感针织开衫",
                slug="cloud-knit-cardigan",
                description="柔软亲肤，适合日常叠穿。",
                fabric_info="粘胶纤维与锦纶",
                care_instructions="平铺晾干，避免长时间暴晒",
                status="published",
            ),
            Product(
                category_id=category.id,
                name="城市机能夹克",
                slug="urban-utility-jacket",
                description="简洁廓形，兼顾通勤与周末活动。",
                fabric_info="再生尼龙",
                care_instructions="局部污渍及时擦拭",
                status="published",
            ),
        ]
        session.add_all(products)
        session.flush()
        for index, product in enumerate(products, start=1):
            sku = ProductSku(
                product_id=product.id,
                color_id=colors[(index - 1) % len(colors)].id,
                size_id=sizes[1].id,
                code=f"FR-{index:03d}-M",
                sale_price=Decimal(str(299 + index * 100)),
                original_price=Decimal(str(399 + index * 100)),
            )
            session.add(sku)
            session.flush()
            session.add(Inventory(sku_id=sku.id, quantity=20, available_quantity=20, locked_quantity=0))
            session.add(SizeChart(product_id=product.id, size_id=sizes[1].id, measurements="胸围 108cm；衣长 70cm"))
    session.commit()


if __name__ == "__main__":
    from app.db.session import get_sync_db_session

    with next(get_sync_db_session()) as session:
        seed_database(session)
