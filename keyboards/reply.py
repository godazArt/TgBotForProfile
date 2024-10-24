from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

del_kb = ReplyKeyboardRemove()

def keyboardBuilder(
        *btns:str,
        placeholder:str = None,
        request_contact:int = None,
        request_location:int = None,
        sizes:tuple[int] = (2,),
):
    if btns:
        keyboard = ReplyKeyboardBuilder()
        
        for i, text in enumerate(btns, start=0):
            if request_contact and request_contact == i:
                keyboard.add(KeyboardButton(text=text,request_contact=True))
            elif request_location and request_location == i:
                keyboard.add(KeyboardButton(text=text,request_location=True))
            else:
                keyboard.add(KeyboardButton(text=text))
        return keyboard.adjust(*sizes).as_markup(
            resize_keyboard=True, input_field_placeholder=placeholder)
    return del_kb


