import app.quiz as quiz
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (Message, ReplyKeyboardMarkup, InlineKeyboardButton,
                           KeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove)
from bot_dp import bot

router = Router()
is_passed = False
is_passing = False
data = []
res = []
question_count = 0
scores = 0
max_scores = 0
@router.message(CommandStart())
async def cmd_start(message: Message):
    global data, max_scores
    data = []
    await message.answer('Добро пожаловать!', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Начать')]], resize_keyboard=True, one_time_keyboard=True))
    with open('app/Вопросы для викторины.txt', 'r', encoding='UTF-8') as file:
        n = int(file.readline())
        for i in range(n):
            quest = dict()
            quest['question'] = file.readline()[:-1]
            quest['cost'] = int(quest['question'].split()[-2][1:])
            quest['answers'] = []
            x = file.readline()
            while not x.startswith('Правильный ответ'):
                quest['answers'].append(x[:-1])
                x = file.readline()
            quest['correct'] = x.split(': ')[-1]
            if quest['correct'].endswith('\n'):
                quest['correct'] = quest['correct'][:-1]
            data.append(quest)
            max_scores += quest['cost']


@router.message(F.text == 'Начать')
async def begin(message: Message):
    global is_passed, res, question_count, scores, is_passing, max_scores
    if res != data:
        res = data.copy()
        is_passed = False
    if is_passed:
        await message.answer(f'Второй раз проходить тот же тест нельзя. Ваш результат {scores}/{max_scores}', reply_markup=ReplyKeyboardRemove())
        return
    if is_passing:
        return
    is_passing = True
    question_count = 0
    scores = 0
    await my_func(message)

@router.callback_query(F.data == "True")
async def right(callback: CallbackQuery):
    global scores
    await callback.answer('')
    await remove_inline_keyboard(callback.message)
    await callback.message.answer(f'Ваш ответ: {}. Это правильный ответ.')
    scores += res[question_count-1]['cost']
    await my_func(callback.message)

@router.callback_query(F.data == "False")
async def wrong(callback: CallbackQuery):
    await callback.answer('')
    await remove_inline_keyboard(callback.message)
    await callback.message.answer(f'Ваш ответ: {}. Это неправильный ответ. Правильный ответ: {res[question_count-1]['correct']}')
    await my_func(callback.message)


async def my_func(message: Message):
    global question_count
    if question_count < len(data):
        question = res[question_count]['question']
        correct = res[question_count]['correct']
        cost = res[question_count]['cost']
        inline_keyboard = []
        quest1 = quiz.Question(question, [], cost)
        for element in res[question_count]['answers']:
            quest1.answers.append(quiz.Answer(text=element, correct=element==correct))
            inline_keyboard.append([InlineKeyboardButton(text=quest1.answers[-1].text, callback_data=f"{quest1.answers[-1].correct}")])
        await message.answer(quest1.text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard))
        question_count += 1
    else:
        await ending(message)

async def ending(message: Message):
    global is_passed, is_passing
    is_passed = True
    is_passing = False
    await message.answer(f'Игра окончена. Ваш результат: {scores}/{max_scores}')

async def remove_inline_keyboard(message: Message):

    await bot.edit_message_reply_markup(chat_id=message.chat.id,

        message_id=message.message_id)