import math
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import  Cart, Category, Item, Order, Prices, User



# class Paginator:
#     def __init__(self, array: list | tuple, page: int=1, per_page: int=1):
#         self.array = array
#         self.per_page = per_page
#         self.page = page
#         self.len = len(self.array)
#         # math.ceil - округление в большую сторону до целого числа
#         self.pages = math.ceil(self.len / self.per_page)

#     def __get_slice(self):
#         start = (self.page - 1) * self.per_page
#         stop = start + self.per_page
#         return self.array[start:stop]

#     def get_page(self):
#         page_items = self.__get_slice()
#         return page_items

#     def has_next(self):
#         if self.page < self.pages:
#             return self.page + 1
#         return False

#     def has_previous(self):
#         if self.page > 1:
#             return self.page - 1
#         return False

#     def get_next(self):
#         if self.page < self.pages:
#             self.page += 1
#             return self.get_page()
#         raise IndexError(f'Next page does not exist. Use has_next() to check before.')

#     def get_previous(self):
#         if self.page > 1:
#             self.page -= 1
#             return self.__get_slice()
#         raise IndexError(f'Previous page does not exist. Use has_previous() to check before.')


# ############### Работа с баннерами (информационными страницами) ###############   

# async def orm_add_banner_description(session: AsyncSession, data: dict):
#     #Добавляем новый или изменяем существующий по именам
#     #пунктов меню: main, about, cart, shipping, payment, catalog
#     query = select(Banner)
#     result = await session.execute(query)
#     if result.first():
#         return
#     session.add_all([Banner(name=name, description=description) for name, description in data.items()]) 
#     await session.commit()


# async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
#     query = update(Banner).where(Banner.name == name).values(image=image)
#     await session.execute(query)
#     await session.commit()


# async def orm_get_banner(session: AsyncSession, page: str):
#     query = select(Banner).where(Banner.name == page)
#     result = await session.execute(query)
#     return result.scalar()


# async def orm_get_info_pages(session: AsyncSession):
#     query = select(Banner)
#     result = await session.execute(query)
#     return result.scalars().all()


############################ Категории ######################################

async def orm_get_categories_names(session: AsyncSession):
    query = select(Category.name)
    result = await session.execute(query)
    return result.scalars().all()
    
async def orm_get_category_id(session:AsyncSession, item_type:str):
    category = await session.execute(select(Category.id).where(Category.name == item_type))
    return category.scalar()

async def orm_get_category_by_id(session:AsyncSession, category_id:int):
    category = await session.execute(select(Category.name).where(Category.id == category_id))
    return category.scalar()

async def orm_get_category_name_by_item_id(session: AsyncSession, item_id):
    item = await orm_get_product(session, item_id)
    query = select(Category.name).where(Category.id == item.category_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_add_categories(session: AsyncSession, categories: str):
    query = select(Category.name)
    result = (await session.execute(query)).scalars().all()
    if categories not in result:
        session.add(Category(name=categories))
     
    await session.commit()


############ Админка: добавить/изменить/удалить товар ########################    

async def orm_add_product(session:AsyncSession, data: dict):
    session.add(Item(
        category_id=data["category"],
        name=data["name"],
        description=data["description"],
        image=data["image"]
    ))
    await session.commit()
    id = await session.execute(select(Item.id).where(Item.category_id == data["category"], Item.name == data["name"], Item.description == data["description"], Item.image == data["image"]))
    return id.scalar()

async def orm_add_prices(session:AsyncSession, item_id: int, data: dict):
    for p in data["price"]:
        temp = p.split('-')
        session.add(Prices(
            item_id=item_id,
            count=int(temp[0]),
            price=float(temp[1])
        ))
    await session.commit()

async def orm_get_products(session:AsyncSession):
    query = select(Item)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_prices(session:AsyncSession, item_id: int):
    query = select(Prices).where(item_id == Prices.item_id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_prices_by_count(session:AsyncSession, item_id: int, count:int):
    query = select(Prices.price).where(item_id == Prices.item_id, count >= Prices.count).order_by(Prices.count.desc())
    result = await session.execute(query)
    return result.scalar()

async def orm_get_products_by_type(session:AsyncSession, item_type:str):
    category = await session.execute(select(Category.id).where(Category.name == item_type))
    category = category.first()
    if(category):
        query = select(Item).where(Item.category_id == category.id)
        result = await session.execute(query)
        return result.scalars().all()
    return []

async def orm_get_product(session:AsyncSession, item_id: int):
    query = select(Item).where(Item.id == item_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_update_prices(session:AsyncSession, item_id: int, data: dict):
    query = delete(Prices).where(Prices.item_id == item_id)
    await session.execute(query)
    await session.commit()
    await orm_add_prices(session, item_id, data)  

async def orm_update_product(session:AsyncSession, item_id: int, data: dict):
    query = update(Item).where(Item.id == item_id).values(
        category_id=data["category"],
        name=data["name"],
        description=data["description"],
        image=data["image"]
    )
    await session.execute(query)
    await session.commit()

async def orm_delete_product(session:AsyncSession, item_id: int):    
    await session.execute(delete(Item).where(Item.id == item_id))
    await session.execute(delete(Prices).where(Prices.item_id == item_id))
    await session.commit()

##################### Добавляем юзера в БД #####################################

async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone)
        )
        await session.commit()


######################## Работа с корзинами #######################################

async def orm_add_to_cart(session: AsyncSession, user_id: int, item_id: int, count: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.item_id == item_id).options(joinedload(Cart.item))
    cart = await session.execute(query)
    cart = cart.scalar()    
    print(user_id," user_id\n\n\n\n",item_id," item_id\n\n\n\n")
    print(cart," cart\n\n\n\n")
    if cart:
        print(" if cart\n\n\n\n")
        price = (await orm_get_prices_by_count(session, item_id, cart.count + count)) * (cart.count + count)
        print(price,"\n\n\n\n")
        cart.count += count
        cart.price = price
        await session.commit()
        return cart
    else:
        print(f"count = {count}",end='\n\n\n\n')
        price = await orm_get_prices_by_count(session, item_id, count) 
        if type(price):
            price = -1
        else:
            price *= count
        session.add(Cart(user_id=user_id, item_id=item_id, count=count, price=price))
        await session.commit()



async def orm_get_user_carts(session: AsyncSession, user_id):
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.item))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    query = delete(Cart).where(Cart.user_id == user_id, Cart.item_id == product_id)
    await session.execute(query)
    await session.commit()

async def orm_get_count_in_cart(session: AsyncSession, user_id: int, product_id: int):
    query = select(Cart.count).where(Cart.user_id == user_id, Cart.item_id == product_id).options(joinedload(Cart.item))
    cart = await session.execute(query)
    return cart.scalar()

async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int, count: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.item_id == product_id).options(joinedload(Cart.item))
    cart = await session.execute(query)
    cart = cart.scalar()
    print(cart, "cart",end='\n\n\n')
    if not cart:
        return True
    if cart.count > count:
        print(cart.count, count, sep='\nразделение\n')
        cart.count -= count
        price = (await orm_get_prices_by_count(session, product_id, cart.count)) * cart.count
        cart.price = price
        await session.commit()
        return False
    else:                
        print(cart.count, count, sep='\nразделение\n')
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return True

########### Заказы ############    
async def orm_add_order(session:AsyncSession, data: dict, user_id: int):
    session.add(Order(
        user_id=user_id,
        address=data["address"],
        delivery_type=data["delivery_type"],
        paymentConfirm=data["paymentConfirm"],
        image=data["image"]
    ))
    await session.commit()
    id = await session.execute(select(Item.id).where(Item.category_id == data["category"], Item.name == data["name"], Item.description == data["description"], Item.image == data["image"]))
    return id.scalar()