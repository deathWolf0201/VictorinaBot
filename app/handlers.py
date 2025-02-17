# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import (Message, ReplyKeyboardMarkup, InlineKeyboardButton,
                           KeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove)

import app.database.requests as rq
import app.quiz as quiz
from bot_dp import bot

router = Router()

data = []
res = []
max_scores = 0
total_questions = 0


@router.message(CommandStart())
async def cmd_start(message: Message):
    global data, max_scores, total_questions, res
    data = []
    max_scores = 0
    with open('app/Вопросы для викторины.txt', 'r', encoding='UTF-8') as file:
        total_questions = int(file.readline().split()[-1])
        for i in range(total_questions):
            quest = dict()
            quest['question'] = file.readline()[:-1]
            quest['cost'] = 1
            if quest['question'].endswith(')'):
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
    if res != data:
        res = data.copy()
        if message.from_user.last_name is not None:
            await rq.set_default(message.from_user.id, message.from_user.first_name + " " + message.from_user.last_name)
        else:
            await rq.set_default(message.from_user.id, message.from_user.first_name)
    else:
        if message.from_user.last_name is not None:
            await rq.set_user(message.from_user.id, message.from_user.first_name + " " + message.from_user.last_name)
        else:
            await rq.set_user(message.from_user.id, message.from_user.first_name)

    if await rq.get_is_passed(message.from_user.id):
        await message.answer(
            f'Второй раз проходить тот же тест нельзя. Ваш результат {await rq.get_scores(message.from_user.id)}/{max_scores} баллов',
            reply_markup=ReplyKeyboardRemove())
        return
    if await rq.get_is_passing(message.from_user.id):
        message_id = await rq.get_last_message_id(message.from_user.id)
        await remove_inline_keyboard(chat_id=message.from_user.id, message_id=message_id)
        await message.answer(
            f'Вы уже проходите тестирование. Вы остановились на {await rq.get_question_count(message.from_user.id)} вопросе из {total_questions}. Нажмите "Продолжить"',
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Продолжить')]], resize_keyboard=True,
                                             one_time_keyboard=True))
        return
    else:
        await message.answer(
            'Добро пожаловать на Кванторину! Ответьте правильно более чем на 8 вопросов и заберите памятный сувенир от Кванториума. Нажмите "Начать", чтобы приступить к тестированию. <b>Внимание</b>: у вас будет только одна попытка.',
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Начать')]], resize_keyboard=True,
                                             one_time_keyboard=True), parse_mode='HTML')


@router.message(F.text == 'Начать')
async def begin(message: Message):
    global res, max_scores

    if await rq.get_is_passing(message.from_user.id):
        await my_func(message)
        return

    await rq.set_is_passing(message.from_user.id)
    await my_func(message)


@router.callback_query(F.data.startswith("True"))
async def right(callback: CallbackQuery):
    await callback.answer('')
    await remove_inline_keyboard(callback.from_user.id, callback.message.message_id)
    await callback.message.answer(f'Это правильный ответ. ')
    await rq.set_scores(callback.from_user.id, res[await rq.get_question_count(callback.from_user.id) - 1]['cost'])
    if await rq.get_question_count(callback.from_user.id) == len(data):
        await ending(callback.from_user.id)
    else:
        await rq.set_question_count(callback.from_user.id, 1)
        await callback.message.answer(f'Нажмите "Далее", чтобы перейти к следующему вопросу.',
                                      reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Далее')]],
                                                                       resize_keyboard=True, one_time_keyboard=True))


@router.callback_query(F.data)
async def wrong(callback: CallbackQuery):
    await callback.answer('')
    await remove_inline_keyboard(callback.from_user.id, callback.message.message_id)
    await callback.message.answer(
        f'Это неправильный ответ. Правильный ответ: {res[await rq.get_question_count(callback.from_user.id) - 1]['correct']}.')
    if await rq.get_question_count(callback.from_user.id) == len(data):
        await ending(callback.from_user.id)
    else:
        await rq.set_question_count(callback.from_user.id, 1)
        await callback.message.answer(f'Нажмите "Далее", чтобы перейти к следующему вопросу.',
                                      reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Далее')]],
                                                                       resize_keyboard=True, one_time_keyboard=True))


@router.message(F.text == 'Продолжить')
@router.message(F.text == 'Далее')
async def my_func(message: Message):
    if await rq.get_last_message_id(message.from_user.id) > 0:
        await remove_inline_keyboard(chat_id=message.from_user.id,
                                     message_id=await rq.get_last_message_id(message.from_user.id))
    question = res[await rq.get_question_count(message.from_user.id) - 1]['question']
    correct = res[await rq.get_question_count(message.from_user.id) - 1]['correct']
    cost = res[await rq.get_question_count(message.from_user.id) - 1]['cost']
    inline_keyboard = []
    quest1 = quiz.Question(question, [], cost)
    for i, element in enumerate(res[await rq.get_question_count(message.from_user.id) - 1]['answers']):
        quest1.answers.append(quiz.Answer(text=element, correct=element == correct))
        inline_keyboard.append(
            [InlineKeyboardButton(text=quest1.answers[-1].text, callback_data=f"{quest1.answers[-1].correct}{i}")])
    msg = await message.answer(
        f"<i><b>{await rq.get_question_count(message.from_user.id)}/{len(data)}</b></i>\n" + quest1.text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard), parse_mode='HTML')
    await rq.set_last_message_id(message.from_user.id, msg.message_id)


@router.message()
async def wrong_message(message: Message):
    await message.answer('Простите, ваша команда не распознана')


async def ending(tg_id):
    await rq.set_is_passed(tg_id)
    if await rq.get_scores(tg_id) / max_scores * 100 > 86:
        await bot.send_message(
            text=f'Викторина завершена. Ваш результат: {await rq.get_scores(tg_id)}/{max_scores} баллов. Поздравляем вас с результатом!',
            reply_markup=ReplyKeyboardRemove(), chat_id=tg_id)
    else:
        await bot.send_message(
            text=f'Викторина завершена. Ваш результат: {await rq.get_scores(tg_id)}/{max_scores} баллов. Спасибо, что поучаствовали в нашей викторине! К сожалению, вам не хватило баллов до победы.',
            reply_markup=ReplyKeyboardRemove(), chat_id=tg_id)


async def remove_inline_keyboard(chat_id, message_id):
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        return
