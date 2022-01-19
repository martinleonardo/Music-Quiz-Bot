import random
import string

import discord
from discord import FFmpegPCMAudio, ClientException
from discord.ext import commands


class WordQuiz(commands.Cog):
    def __init__(self, client):
        self.client = client

    word_list = []
    guessed_words = []
    current_word = ''
    letters = []
    letters_correct = [False, False, False, False, False]
    letters_in_incorrect_spot = []
    alphabet_string = string.ascii_uppercase
    letters_other = list(alphabet_string)
    hint = ''

    @commands.Cog.listener()
    async def on_ready(self):
        with open('cogs/words_alpha.txt') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            self.word_list.append(line)

        await self.refresh_word()

    @commands.command(description="guess word")
    async def guess(self, ctx, *, word):
        word = word.upper()
        if word == self.current_word:
            await ctx.send('Correct! The word was: ' + self.current_word + '. It took ' + str(len(self.guessed_words)+1) + '/6 tries')
            await self.refresh_word()
            return
        if len(word) != 5:
            await ctx.send('Invalid word length. Must be 5 letters.')
            return
        if word not in self.word_list:
            await ctx.send('Invalid word.')
            return
        if word in self.guessed_words:
            await ctx.send('Word has already been guessed.')
            return
        self.guessed_words.append(word)
        letters_copy = self.letters
        for i in range(len(word)):
            if word[i] == self.current_word[i]:
                if word[i] in letters_copy:
                    letters_copy.remove(word[i])
        for i in range(len(word)):
            if word[i] == self.current_word[i]:
                self.hint += '__**' + word[i] + '**__'
                self.letters_correct[i] = True
                if word[i] in self.letters_in_incorrect_spot:
                    self.letters_in_incorrect_spot.remove(word[i])
            elif word[i] in letters_copy:
                self.hint += '***' + word[i] + '***'
                if word[i] not in self.letters_in_incorrect_spot:
                    self.letters_in_incorrect_spot.append(word[i])
                letters_copy.remove(word[i])
            else:
                self.hint += word[i]
            if word[i] in self.letters_other:
                self.letters_other.remove(word[i])
            self.hint += ' '
        self.hint += '\n'
        await ctx.send('Guess ' + str(len(self.guessed_words)) + '/6.\n' + self.hint)

        if len(self.guessed_words) > 5:
            await ctx.send('Nice try! You have run out of guesses. The word was : ' + self.current_word + '\nNew word is being generated.')
            await self.refresh_word()

    @commands.command(description="new word")
    async def new_word(self, ctx):
        await ctx.send('The word was : ' + self.current_word + '\nA new word has been generated! Enjoy!')
        await self.refresh_word()

    @commands.command(description="check if valid word")
    async def word_check(self, ctx, *words):
        response = 'The following words are valid:\n'
        for word in words:
            word = word.upper()
            if word in self.word_list:
                response += word + '\n'
        if response == 'The following words are valid:\n':
            response = 'No valid words given.'
        await ctx.send(response)

    @commands.command(description="reveal word")
    async def reveal(self, ctx):
        print('Word: ' + self.current_word)

    @commands.command(description="print remaining letters")
    async def remaining_letters(self, ctx):
        response = 'Letters in correct place:\n'
        for i in range(len(self.letters_correct)):
            if self.letters_correct[i]:
                response += str(await self.emoji(self.current_word[i]))
            else:
                response += ':blue_square:'
        response += '\nLetters in incorrect place:\n'
        for letter in self.letters_in_incorrect_spot:
            response += '***' + letter + '*** '
        response += '\nLetters left to guess:\n'
        for letter in self.letters_other:
            response += '' + letter + ' '
        await ctx.send(response)

    async def emoji(self, letter):
        return ':regional_indicator_' + letter.lower() + ':'

    async def refresh_word(self):
        self.letters_correct = [False, False, False, False, False]
        self.letters_in_incorrect_spot = []
        self.letters_other = list(self.alphabet_string)
        self.guessed_words = []
        self.hint = ''
        await self.random_word()

    async def random_word(self):
        self.current_word = random.choice(self.word_list).upper()
        self.letters = []
        for i in range(len(self.current_word)):
            self.letters.append(self.current_word[i])

def setup(client):
    client.add_cog(WordQuiz(client))