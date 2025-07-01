from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, CommandStart, or_f
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_product, orm_add_categories, orm_delete_product, orm_get_categories_names, orm_get_category_by_id, orm_get_category_id, orm_get_products, orm_get_product, orm_update_prices, orm_update_product, orm_get_prices, orm_add_prices

from filters.chat_types import ChatTypeFilter, IsAdmin
from keyboards.inline import get_callback_btns
from keyboards.reply import keyboardBuilder, del_kb
from common.bot_cmds_list import categories


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


ADMIN_START_KB = keyboardBuilder(
                             "Каталог 📖",
                             "Корзина 🛒",
                             "Заказы 📦",
                             "О магазине 📋",
                             "Поддержка 📞",
                             "Возможности администратора🍏",
                             placeholder="Выберите интересующий вас раздел",
                             sizes=(3,2)
                         )

ADMIN_KB = keyboardBuilder(
    "Добавить товар",
    "Все товары",
    "Назад в меню",
    placeholder="Выберите действие",
    sizes=(2, 1),
)

class AddProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    image = State()
    
    price_list = []
    item_for_change = None

    texts = {
            'AddProduct:name': 'Введите название заново:',
            'AddProduct:description': 'Введите описание заново:',
            'AddProduct:price': 'Введите стоимость заново:',
            'AddProduct:image': 'Этот стейт последний, поэтому...',
            }


@admin_router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Привет, я бот обрабатывающий тестовый магазин", reply_markup=ADMIN_START_KB)

@admin_router.message(or_f(Command('menu'), F.text.lower().contains('меню') ))
async def menu(message: types.Message, state: FSMContext):
    await message.answer("Меню:", reply_markup=ADMIN_START_KB)
    await state.clear()
    


@admin_router.message(or_f(Command("admin"), F.text == "Возможности администратора🍏"))
async def add_product(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Все товары")
async def change_product(message: types.Message, session:AsyncSession):
    for item in await orm_get_products(session):
        price_str = "При покупке :"            
        for price in await orm_get_prices(session, item.id):   
            price_str += f"\nОт {price.count} шт. Цена - {round(price.price, 2)}руб."            
        await message.answer_photo(item.image, caption=f"<strong>Id товара: {item.id}\nНазвание: {item.name}\n</strong>Тип: {await orm_get_category_by_id(session, item.category_id)}\n{item.description}\n<strong>Стоимость:\n{price_str}</strong>",
                                   reply_markup=get_callback_btns(btns={
                'Удалить':f'delete_{item.id}',
                'Изменить':f'change_{item.id}'
            }))
    await message.answer("Вот все товары⏫")
    


@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    item_id = callback.data.replace("delete_","")    
    try:
        await orm_delete_product(session=session, item_id=int(item_id))

        await callback.answer("Товар удален")
        await callback.message.answer("Товар удален")
        await callback.message.delete()
    except Exception as e:
        await callback.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=ADMIN_KB
        )
        await callback.message.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=ADMIN_KB
        )


@admin_router.callback_query(StateFilter(None),F.data.startswith('change_'))
async def update_product(callback: types.CallbackQuery,state:FSMContext, session: AsyncSession):
    item_id = callback.data.replace("change_","")
    
    try:
        item_for_change = await orm_get_product(session, int(item_id))
        AddProduct.item_for_change = item_for_change
        await callback.answer()
        await callback.message.answer("Если не хотите вносить изменения в определённой категории отправьте '.'.\nВведите тип товара", 
                                      reply_markup=keyboardBuilder(*categories, placeholder="Выберите необходимую категорию", sizes=(2,)))
        await state.set_state(AddProduct.type)
    except Exception as e:
        await callback.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=ADMIN_KB
        )
        await callback.message.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=ADMIN_KB
        )


@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext, session: AsyncSession):
    orm_get_categories_names(session)
    await message.answer("Вы начали процесс добавления товаров.\nДля отмены напишите 'отмена', a для возвращения к предыдущему шагу 'назад'")
    await message.answer("Выберите необходимую категорию, или введите новую, если нет необходимой", reply_markup=keyboardBuilder(*(await orm_get_categories_names(session)),
                             placeholder="Выберите необходимую категорию, или введите новую, если нет необходимой",
                             sizes=(4,)))
    await state.set_state(AddProduct.category)



@admin_router.message(StateFilter('*'),Command("отмена"))
@admin_router.message(StateFilter('*'),F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    cur_state = await state.get_state()

    if cur_state is None:
         return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)

@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def back_handler(message: types.Message, state: FSMContext) -> None:
    cur_state = await state.get_state()
    if cur_state == AddProduct.name:
         await message.answer(f"Предыдущего шага нет, или введите название товара или напишите 'отмена'")
         return

    previous = None
    for step in AddProduct.__all_states__:
        if step.state == cur_state:
            await state.set_state(previous)
            await message.answer(f"Вы вернулись к прошлому шагу\n{AddProduct.texts[previous.state]}")
            return
        previous = step



@admin_router.message(AddProduct.category, or_f(F.text, F.text == '.'))
async def add_type(message: types.Message, state: FSMContext, session:AsyncSession):
    if message.text == ".":
        await state.update_data(category=AddProduct.item_for_change.category_id)
        await message.answer("Введите название товара",reply_markup=del_kb)
        await state.set_state(AddProduct.name)
    else:
        if(message.text not in await orm_get_categories_names(session)):
            await orm_add_categories(session=session, categories=message.text)
        await state.update_data(category=await orm_get_category_id(session, message.text))
        await message.answer("Введите название товара",reply_markup=del_kb)
        await state.set_state(AddProduct.name)

@admin_router.message(AddProduct.category)
async def add_type(message: types.Message, state: FSMContext, session:AsyncSession):
    await message.answer("Вы ввели недопустимые данные, введите категорию товара",
                        reply_markup=keyboardBuilder(*(await orm_get_categories_names(session)),
                        placeholder="Выберите необходимую категорию",
                        sizes=(4,)))


@admin_router.message(AddProduct.name, or_f(F.text, F.text == '.'))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(name=AddProduct.item_for_change.name)
    else:
        await state.update_data(name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(AddProduct.description)

@admin_router.message(AddProduct.name)
async def add_name(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите название товара")


@admin_router.message(AddProduct.description, or_f(F.text, F.text == "."))
async def add_description(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(description=AddProduct.item_for_change.description)
    else:
        await state.update_data(description=message.text)
    await message.answer("Введите стоимость товара.\nФормат ввода: '5-100' - это значит при покупке от 5 шт. и больше цена за ед. товара 100 рублей. Если хотите прекратить ввод цен, напишите 'все'.")
    await state.set_state(AddProduct.price)

@admin_router.message(AddProduct.description)
async def add_description(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите описание товара")

###ДОДЕЛАТЬ!!!!
@admin_router.message(AddProduct.price,or_f(F.text, F.text == "."))
async def add_price(message: types.Message, state: FSMContext, session:AsyncSession):
    if message.text == ".":
        for price in await orm_get_prices(session, AddProduct.item_for_change.id):
            AddProduct.price_list.append(f"{price.count}-{price.price}")
        await state.update_data(price=AddProduct.price_list)
        await state.set_state(AddProduct.image)
        await message.answer("Загрузите изображение товара")

    elif  message.text.lower() == "все":
        await state.update_data(price=AddProduct.price_list)
        await state.set_state(AddProduct.image)
        await message.answer("Загрузите изображение товара")

    else:
        try:
            temp = message.text.split('-')
            int(temp[0])
            float(temp[-1])
            AddProduct.price_list.append(message.text)
            await message.answer("Введите ещё цену или напишите 'все'")
        except ValueError:
            await message.answer("Введите корректное значение цены.\nФормат ввода: '5-100' - это значит при покупке от 5 шт. и больше цена за ед. товара 100 рублей. Если хотите прекратить ввод цен, напишите 'все'.")
            return     
    

@admin_router.message(AddProduct.price)
async def add_price(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите цену товара")


@admin_router.message(AddProduct.image,or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session:AsyncSession):
    if message.text and message.text == ".":
        await state.update_data(image=AddProduct.item_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    try:
        if AddProduct.item_for_change:
            await orm_update_product(session, AddProduct.item_for_change.id, data)
            await orm_update_prices(session, AddProduct.item_for_change.id, data)
        else:
            id = await orm_add_product(session, data)
            await orm_add_prices(session, id, data)
            
        await message.answer("Товар добавлен/изменен", reply_markup=ADMIN_KB)        

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, чтобы решить её", reply_markup=ADMIN_KB
        )
    await state.clear()
    AddProduct.item_for_change = None
    AddProduct.price_list = []

@admin_router.message(AddProduct.image)
async def add_image(message: types.Message, state: FSMContext):
    await message.answer("Вы должны отправить изображение")