# HangMan.py
import logging
import random
from aiogram import Bot
import app.keyboards as kb
import app.oxford_api as ox


class HangmanGame:

    def __init__(self, user_name, chat_id, difficulty):
        self.name = user_name
        self.chat_id = chat_id
        self.difficulty = difficulty
        self.word = random.choice(self.load_words(difficulty))
        self.guessed_letters = set()
        self.wrong_guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong_guesses = {'easy': 8, 'medium': 7, 'hard': 6}[difficulty]
        self.hints_used = 0
        self.used_definition = False
        self.state = None

    async def start_game(self, bot: Bot):
        await bot.send_message(self.chat_id, self.get_display_word())
        await bot.send_message(self.chat_id, "Guess a letter:")

    def get_display_word(self):
        display_word = ' '.join([letter if letter in self.guessed_letters else '_' for letter in self.word])
        return display_word

    async def handle_guess(self, bot: Bot, letter):
        if letter in self.guessed_letters:
            await bot.send_message(self.chat_id, f"You already guessed the letter '{letter}'. Try again.")
        elif letter in self.word:
            self.guessed_letters.add(letter)
            if self.is_word_guessed():
                await self.handle_game_end(bot)
            else:
                await bot.send_message(self.chat_id, self.get_display_word())
        elif letter in self.wrong_guessed_letters:
            await bot.send_message(self.chat_id, f"You already tried the letter '{letter}'. Try something else.")
        else:
            self.wrong_guesses += 1
            self.wrong_guessed_letters.add(letter)
            if self.wrong_guesses >= self.max_wrong_guesses:
                await self.handle_game_end(bot)
            else:
                await bot.send_message(self.chat_id,
                                       f"Wrong guess! You have {self.max_wrong_guesses - self.wrong_guesses} guesses left.")
                if not self.used_definition:
                    await self.suggesting_definition(bot)
                elif self.hints_used < 2:
                    await self.suggesting_hint(bot)

                await bot.send_message(self.chat_id, self.get_display_word())

    async def suggesting_definition(self, bot: Bot):
        await bot.send_message(self.chat_id, text='Would you like definitions and examples of how the word is used?',
                               reply_markup=kb.definitions)

    async def suggesting_hint(self, bot: Bot):
        await bot.send_message(self.chat_id, text='Would you like a random letter in your word to be revealed?',
                               reply_markup=kb.hint)

    async def handle_game_end(self, bot: Bot):
        # Display game result
        from app.db import save_score
        points = self.calculate_points()

        await save_score(self.chat_id, self.name, points)

        if self.is_word_guessed():
            message = f"Congratulations! You've guessed the word: {self.word}\nWould you like to play again?"
        else:
            message = f"Game over! The word was: {self.word}\nWould you like to play again?"
        await bot.send_message(self.chat_id, message, reply_markup=kb.resetting)

    async def reset_game_state(self):
        self.used_definition = False
        self.word = random.choice(self.load_words(self.difficulty))
        self.guessed_letters = set()
        self.wrong_guessed_letters = set()
        self.wrong_guesses = 0
        self.hints_used = 0
        self.state = None

    async def give_definition(self, bot: Bot):
        result = await ox.get_data(self.word, True)
        if result:
            self.used_definition = True
            await bot.send_message(self.chat_id, text='Definitions:\n')
            for i in range(len(result['definitions'])):
                await bot.send_message(self.chat_id, text=f"{i + 1}) {result['definitions'][i]}")
            if result['examples']:
                await bot.send_message(self.chat_id, text='Examples:\n')
                for i in range(len(result['examples'])):
                    await bot.send_message(self.chat_id, text=f"{i + 1}) {result['examples'][i]}")

    async def give_hint(self, bot: Bot):
        available_letters = [letter for letter in self.word if letter not in self.guessed_letters]

        if available_letters:
            hint_letter = random.choice(available_letters)
            self.guessed_letters.add(hint_letter)
            self.hints_used += 1
            await bot.send_message(self.chat_id, f"Hint: The word contains the letter '{hint_letter}'.")
            if len(set(available_letters)) == 1:
                await self.handle_game_end(bot)
            else:
                await bot.send_message(self.chat_id, self.get_display_word())
        else:
            await bot.send_message(self.chat_id, "No hint available.")

    def calculate_points(self):
        if len(self.guessed_letters) == len(set(self.word)):
            difficulty_multiplier = {
                'hard': 2,
                'medium': 1.6,
                'easy': 1.2
            }.get(self.difficulty, 1)

            hints_multiplier = {
                0: 1.5,
                1: 1.2,
                2: 1
            }.get(self.hints_used, 1)

            word_length_multiplier = 1.2 if len(set(self.word)) >= 3 else 1

            multiplier = 10 * difficulty_multiplier * hints_multiplier * word_length_multiplier
            points = round(multiplier)
        else:
            difficulty_multiplier = {
                'hard': 1.2,
                'medium': 1.5,
                'easy': 2
            }.get(self.difficulty, 1)

            hints_multiplier = {
                0: 1,
                1: 1.5,
                2: 2
            }.get(self.hints_used, 1)

            word_length_multiplier = 1.2 if len(set(self.word)) <= 3 else 1

            multiplier = -10 * difficulty_multiplier * hints_multiplier * word_length_multiplier
            points = round(multiplier)

        return points

    def load_words(self, difficulty):
        path = f'words_fold/{difficulty}.txt'
        with open(path, 'r') as file:
            words = [line.split()[0].strip() for line in file if len(line.split()[0].strip()) >= 3]
        return words

    def is_word_guessed(self):
        return all(letter in self.guessed_letters for letter in self.word)
