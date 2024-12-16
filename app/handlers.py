# -*- coding: utf-8 -*-

import app.quiz as quiz
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (Message, ReplyKeyboardMarkup, InlineKeyboardButton,
                           KeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove)
from bot_dp import bot
import app.database.requests as rq
router = Router()

data = []
res = []
max_scores = 0
@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id, message.from_user.first_name+" "+message.from_user.last_name)
    global data, max_scores
    data = []
    max_scores = 0
    await message.answer('Добро пожаловать! Нажмите "Начать", чтобы приступить к тестированию. Внимание: тестирование проходится только 1 раз.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Начать')]], resize_keyboard=True, one_time_keyboard=True))
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
    global res, max_scores
    if res != data:
        res = data.copy()
        await rq.set_default(message.from_user.id)
    if await rq.get_is_passed(message.from_user.id):
        await message.answer(f'Второй раз проходить тот же тест нельзя. Ваш результат {await rq.get_scores(message.from_user.id)}/{max_scores}', reply_markup=ReplyKeyboardRemove())
        return
    if await rq.get_is_passing(message.from_user.id):
        return
    await rq.set_is_passing(message.from_user.id)
    await my_func(message)

@router.callback_query(F.data == "True")
async def right(callback: CallbackQuery):
    await callback.answer('')
    await remove_inline_keyboard(callback.message)
    await callback.message.answer(f'Это правильный ответ. Нажмите "Далее", чтобы перейти к следующему вопросу.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Далее')]], resize_keyboard=True, one_time_keyboard=True))
    await rq.set_scores(callback.from_user.id, res[await rq.get_question_count(callback.from_user.id)-1]['cost'])


@router.callback_query(F.data == "False")
async def wrong(callback: CallbackQuery):
    await callback.answer('')
    await remove_inline_keyboard(callback.message)
    await callback.message.answer(f'Это неправильный ответ. Правильный ответ: {res[await rq.get_question_count(callback.from_user.id)-1]['correct']}. Нажмите "Далее", чтобы перейти к следующему вопросу.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Далее')]], resize_keyboard=True, one_time_keyboard=True))



@router.message(F.text == 'Далее')
async def my_func(message: Message):
    if await rq.get_question_count(message.from_user.id) < len(data):
        await rq.set_question_count(message.from_user.id, 1)
        question = res[await rq.get_question_count(message.from_user.id)-1]['question']
        correct = res[await rq.get_question_count(message.from_user.id)-1]['correct']
        cost = res[await rq.get_question_count(message.from_user.id)-1]['cost']
        inline_keyboard = []
        quest1 = quiz.Question(question, [], cost)
        for element in res[await rq.get_question_count(message.from_user.id)-1]['answers']:
            quest1.answers.append(quiz.Answer(text=element, correct=element==correct))
            inline_keyboard.append([InlineKeyboardButton(text=quest1.answers[-1].text, callback_data=f"{quest1.answers[-1].correct}")])
        await message.answer(quest1.text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard))

    else:
        await ending(message)

@router.message()
async def wrong_message(message: Message):
    await message.answer('Простите, ваша команда не распознана')

async def ending(message: Message):
    await rq.set_is_passed(message.from_user.id)
    await message.answer(f'Игра окончена. Ваш результат: {await rq.get_scores(message.from_user.id)}/{max_scores}', reply_markup=ReplyKeyboardRemove())

async def remove_inline_keyboard(message: Message):
    await bot.edit_message_reply_markup(chat_id=message.chat.id,message_id=message.message_id)