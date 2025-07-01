from aiogram.types  import BotCommand

categories = ['text']

private = [
    BotCommand(command='start', description='Начать общение'),
    BotCommand(command='menu', description='Меню'),
    BotCommand(command='catalog', description='Просмотреть каталог'),
    BotCommand(command='orders', description='Заказы'),
    BotCommand(command='cart', description='Корзина'),
    BotCommand(command='about', description='О нашей компании'),
    BotCommand(command='shipping', description='Варианты доставки'),
    BotCommand(command='support', description='Поддержка'),
]