from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, or_f, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter
from keyboards import reply
from database.orm_query import orm_add_to_cart, orm_add_user, orm_get_categories_names, orm_get_category_by_id, orm_get_count_in_cart, orm_get_prices, orm_get_product, orm_get_products, orm_get_products_by_type, orm_get_user_carts, orm_reduce_product_in_cart
from keyboards.inline import get_callback_btns
from common import bot_cmds_list


user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))


START_KB = reply.keyboardBuilder(
                             "Каталог 📖",
                             "Корзина 🛒",
                             "Заказы 📦",
                             "О магазине 📋",
                             "Поддержка 📞",
                             placeholder="Выберите интересующий вас раздел",
                             sizes=(3,)
                         )

class Catalog(StatesGroup):
    category = State()

class Order(StatesGroup):
    delivery_type = State()
    address = State()
    paymentConfirm = State()

@user_private_router.message(StateFilter('*'), Command("menu"))
@user_private_router.message(StateFilter('*'), F.text.lower().contains('меню'))
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Меню:", reply_markup=START_KB)

@user_private_router.message(CommandStart())
async def start_handler(message: types.Message, session:AsyncSession, state: FSMContext):
    await message.answer(f"Привет, я бот обрабатывающий тестовый магазин", 
                         reply_markup=START_KB)
    await state.clear()
    await orm_add_user(session=session, user_id=message.from_user.id)

    


@user_private_router.message( or_f(Command('catalog'), F.text== "Каталог 📖"))
async def catalog(message: types.Message, state: FSMContext, session:AsyncSession):
    await message.answer("Каталог:", reply_markup=reply.keyboardBuilder(*(await orm_get_categories_names(session)),"Назад в меню",
                             placeholder="Выберите интересующую вас категорию",
                             sizes=(4,)))  
    await state.set_state(Catalog.category)
    print(bot_cmds_list.categories,end='\n\n\n\n\n')
    bot_cmds_list.categories = await orm_get_categories_names(session)
    print(type(bot_cmds_list.categories),end='\n\n\n\n\n')


@user_private_router.message(Catalog.category, F.text)
async def see_catalog(message: types.Message, state: FSMContext, session:AsyncSession):    
    bot_cmds_list.categories
    if(message.text in bot_cmds_list.categories):
        for item in await orm_get_products_by_type(session, message.text):
            price_str = "При покупке от:"            
            for price in await orm_get_prices(session, item.id):   
                price_str += f"\nОт {price.count} шт. Цена - {round(price.price, 2)}руб."
            await message.answer_photo(item.image, caption=f"<strong>Id товара: {item.id}\nНазвание: {item.name}\n</strong>Тип: {await orm_get_category_by_id(session, item.category_id)}\n{item.description}\n<strong>Стоимость:\n{price_str}</strong>",
                                   reply_markup=get_callback_btns(btns={
                'Добавить в корзину 1 шт':f'add_cart_{item.id}-1',
                'Добавить 5 шт':f'add_cart_{item.id}-5',
                'Добавить 10 шт':f'add_cart_{item.id}-10',
                'Добавить 25 шт':f'add_cart_{item.id}-25'                
            },sizes=(1,3)))
        await message.answer("Вот все товары из этой категории⏫",reply_markup=reply.keyboardBuilder(*(await orm_get_categories_names(session)),"Назад в меню",
                             placeholder="Выберите интересующую вас категорию",
                             sizes=(4,)))  
    else:
        await message.answer("Вы ввели несуществующий тип товара, выберите из предложенных вариантов", reply_markup=reply.keyboardBuilder(*(await orm_get_categories_names(session)),"Назад в меню",
                             placeholder="Выберите интересующую вас категорию",
                             sizes=(4,)))  


@user_private_router.message(Catalog.category)
async def see_catalog(message: types.Message, session:AsyncSession):
    await message.answer("Вы ввели недопустимые данные, введите категорию товара",
                        reply_markup=reply.keyboardBuilder(*(await orm_get_categories_names(session)),
                        placeholder="Выберите необходимую категорию",
                        sizes=(4,)))


@user_private_router.callback_query(F.data.startswith('add_cart_'))
async def add_product_to_cart(callback: types.CallbackQuery, session: AsyncSession):
    item_id = callback.data.replace("add_cart_","")
    print(f"item_id = {item_id}",end='\n\n\n\n')
    try:
        item_id, count = item_id.split('-')
        print(f"item_id = {item_id}, count = {count}",end='\n\n\n\n')
        await orm_add_to_cart(session=session, item_id=int(item_id), count=int(count), user_id=callback.from_user.id)

        await callback.answer("Товар добавлен в корзину")
        await callback.message.answer("Товар добавлен в корзину")
    except Exception as e:
        await callback.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=reply.keyboardBuilder(*(await orm_get_categories_names(session)),"Назад в меню",
                             placeholder="Выберите интересующую вас категорию",
                             sizes=(4,)))
        
        await callback.message.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=reply.keyboardBuilder(*(await orm_get_categories_names(session)),"Назад в меню",
                             placeholder="Выберите интересующую вас категорию",
                             sizes=(4,)))
        
@user_private_router.callback_query(F.data.startswith('del_cart_'))
async def del_product_from_cart(callback: types.CallbackQuery, session: AsyncSession):
    item_id = callback.data.replace("del_cart_","")
    try:
        item_id, count = item_id.split('-')
        print(item_id, " item_id ", count, " count ",end='\n\n\n')
        logic = await orm_reduce_product_in_cart(session=session, product_id=int(item_id),count=int(count), user_id=callback.from_user.id)
        if logic:
            await callback.message.delete()
            await callback.answer("Товар удален из корзины")
            await callback.message.answer("Товар удален из корзины")
        else:
            await callback.message.delete()
            await callback.answer(f"Количество товара в корзине уменьшенно")    
###########
        
    except Exception as e:
        await callback.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=reply.keyboardBuilder("Назад в меню"))
        
        await callback.message.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=reply.keyboardBuilder("Назад в меню"))


@user_private_router.message(or_f(Command('orders'), F.text == "Заказы 📦"))
async def order(message: types.Message):
    await message.answer("Ваши заказы:", reply_markup=reply.keyboardBuilder(
                             "Назад в меню 📖",
                             placeholder="Выберите интересующий вас заказ"
                         ),)
    
@user_private_router.message( F.text == "Оформить заказ")
async def active_orders(message: types.Message, state: FSMContext):
    state.set_state(Order.delivery_type)
    await message.answer("Укажите каким способом отправить товар.", reply_markup=reply.keyboardBuilder(
                            "СДЭК📗",
                            "Почта России🦅",
                            "Назад в меню 📖",
                            placeholder="Выберите интересующий вас заказ"
                         ),)
    

@user_private_router.message(Order.delivery_type, F.text)
async def add_delivery(message: types.Message, state: FSMContext):
    
    await state.update_data(delivety_type=message.text)
    await message.answer("Введите адрес доставки(Фамилия, Имя, Отчество, адрес доставки)")
    await state.set_state(Order.address)

@user_private_router.message(Order.delivery_type)
async def add_delivery(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите адрес доставки(Фамилия, Имя, Отчество, адрес доставки)")


@user_private_router.message(Order.address, F.text)#F.photo
async def add_addres(message: types.Message, state: FSMContext):
    
    await state.update_data(addres=message.text)
    await message.answer(f"Отправьте оплату в размере {'заглушка руб.'} на номер {'+79188050062'} и отправьте скриншот")
    await state.set_state(Order.paymentConfirm)

@user_private_router.message(Order.address)
async def add_addres(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте скриншот подтверждающий оплату")

@user_private_router.message(Order.paymentConfirm,or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session:AsyncSession):
    
    await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    try:
        id = await orm_add_product(session, data)
        await orm_add_prices(session, id, data)            
        await message.answer("Товар добавлен/изменен", reply_markup=START_KB)        

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=reply.keyboardBuilder(
                            "СДЭК📗",
                            "Почта России🦅",
                            "Назад в меню 📖",
                            placeholder="Выберите интересующий вас заказ"
                         ),)
    await state.clear()

@user_private_router.message(Order.paymentConfirm)
async def add_image(message: types.Message, state: FSMContext):
    await message.answer("Вы должны отправить изображение")


@user_private_router.message(or_f(Command('cart'), F.text == "Корзина 🛒"))
async def cart(message: types.Message, session: AsyncSession):
    items = await orm_get_user_carts(session, message.from_user.id)
    for item in items:
            piece = await orm_get_product(session,item.item_id)
            if(item.price == -1):
                price = "Для данного количества товара нельзя совершить заказ."
            else:
                price = f'{round(item.price,2)} руб.'
            await message.answer_photo(piece.image, caption=f"<strong>Название: {piece.name}\n</strong>Тип: {await orm_get_category_by_id(session, piece.category_id)}\n{piece.description}\n<strong>Количество: {item.count} шт.\nСтоимость:\n{price} </strong>",
                                   reply_markup=get_callback_btns(btns={
                'Удалить из корзины 1 шт':f'del_cart_{item.item_id}-1',
                'Удалить 5 шт':f'del_cart_{item.item_id}-5',
                'Удалить 10 шт':f'del_cart_{item.item_id}-10',
                'Удалить 25 шт':f'del_cart_{item.item_id}-25'                
            },sizes=(1,3)))

    await message.answer("Товары в вашей корзине⏫", reply_markup=reply.keyboardBuilder(
                            "Оформить заказ",
                            "Назад в меню 📖",
                            placeholder="Выберите интересующий вас товар",
                            sizes=(3,)
                         ),)

@user_private_router.message(or_f(Command('shipping'), F.text == "Доставка 🚚"))
async def shipping(message: types.Message):
    await message.answer("Доставка:", reply_markup=reply.keyboardBuilder(
                             "Самовывоз 👷",
                             "Почта России 🇷🇺",
                             "СДЭК 🚛",
                             "BoxBerry 🍇",
                             "Указать номер телефона☎️",
                             "Указать адрес доставки📍",
                             "Назад в меню 📖",
                             placeholder="Выберите интересующуй вас вариант доставки",
                             request_contact=4,
                             request_location=5,
                             sizes=(2,)
                         ),)

@user_private_router.message(or_f(Command('about'), F.text == "О магазине 📋"))
async def about(message: types.Message):
    await message.answer("Наша компания давно зарекомендовала себя на рынке как один из лучших поставщиков.\n"
                         "У нас вы найдёте качественный товар, приятных менеджеров и выгодные предложения.", reply_markup=reply.keyboardBuilder(
                             "Назад в меню 📖",
                         ),)

@user_private_router.message(or_f(Command('support'), F.text == "Поддержка 📞"))
async def support(message: types.Message):
    await message.answer("Контакты для связи:"
                         "Whatsup:\n"
                         "Алексей Иванов +7(011)456-25-97 \n"
                         "Екатерина Петрова +7(011)456-25-97 \n"
                         "Максим Сидоров +7(011)456-25-97 \n")

    await message.answer("Telegram: \n"
                         "Игорь Морозов https://t.me/godazArt1", reply_markup=reply.keyboardBuilder(                             
                             "Оставить заявку для обратной связи📢",
                             "Назад в меню 📖",
                             placeholder="Выберите любого менеджера",
                             sizes=(1,)
                         ),)
