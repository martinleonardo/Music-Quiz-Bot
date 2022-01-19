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
    letters_correct = []
    letters_in_incorrect_spot = []
    alphabet_string = string.ascii_uppercase
    letters_other = list(alphabet_string)

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
            await ctx.send('Correct! The word was: ' + self.current_word + '. It took ' + len(self.guessed_words)+1 + '/6 tries')
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
        hint = ''
        self.guessed_words.append(word)
        for i in range(len(word)):
            if word[i] == self.current_word[i]:
                hint += '__**' + word[i] + '**__'
                self.letters_correct.append(word[i])
            elif word[i] in self.letters:
                hint += '***' + word[i] + '***'
                self.letters_in_incorrect_spot.append(word[i])
            else:
                hint += word[i]
            if word[i] in self.letters_other:
                self.letters_other.remove(word[i])
            hint += ' '
        await ctx.send('Guess ' + str(len(self.guessed_words)) + '/6.\n' + hint)

        if len(self.guessed_words) > 5:
            await ctx.send('Nice try! You have run out of guesses. New word is being generated.')
            await self.refresh_word()

    @commands.command(description="reveal word")
    async def reveal(self, ctx):
        print('Word: ' + self.current_word)

    @commands.command(description="print remaining letters")
    async def remaining_letters(self, ctx):
        response = 'Letters in correct place:\n'
        for letter in self.letters_correct:
            response += '__**' + letter + '**__ '
        response += '\nLetters in incorrect place:\n'
        for letter in self.letters_in_incorrect_spot:
            response += '***' + letter + '*** '
        response += '\nLetters left to guess:\n'
        for letter in self.letters_other:
            response += '' + letter + ' '
        await ctx.send(response)


    async def refresh_word(self):
        self.letters_correct = []
        self.letters_in_incorrect_spot = []
        letters_other = list(self.alphabet_string)
        self.guessed_words = []
        await self.random_word()

    async def random_word(self):
        self.current_word = random.choice(self.word_list).upper()
        self.letters = []
        for i in range(len(self.current_word)):
            self.letters.append(self.current_word[i])

def setup(client):
    client.add_cog(WordQuiz(client))