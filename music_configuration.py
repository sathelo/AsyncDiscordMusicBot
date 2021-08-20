import discord
from discord.ext.commands.core import command
import youtube_dl
from discord import VoiceClient
from discord.ext import commands
from discord.ext.commands import Context
from youtube_dl.utils import DownloadError


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot        
        self.song_list = []
        self.context = None

    async def __playlist(self, ctx: Context = None):
        """ Обработчик плейлиста

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
        """
        # Если передали контекс обновить его иначе оставить старый
        if not ctx is None:
            self.ctx = ctx

        # Если контекста нет, то выходим
        if self.ctx is None:
            return

        # Если нет voice_client, то выходим 
        voice_client: VoiceClient = self.ctx.voice_client
        if not isinstance(voice_client, VoiceClient):
            return


        # TODO: Сделать проверку и запуск музыки из очереди
        if not voice_client.is_playing() and len(self.song_list):
            url = self.song_list.pop(0)
            voice_client.loop.create_task(self.play(self.ctx, url))


        # Добавляем проверку в цикл событий еще раз
        voice_client.loop.create_task(self.__playlist(self.ctx))

    async def __check_access(self, ctx: Context) -> bool:
        """ Проверка доступа к командам

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.

        Returns:
            bool: True - если пользователь в голосов чате
        """
        name = await self.__get_username(ctx)
        if ctx.author.voice:
            return True

        await ctx.send(f"{name} ты не в голосовом канале ⁉")
        return False

    async def __get_username(self, ctx: Context) -> str:
        """ Получить имя пользователя

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.

        Returns:
            str: Для обычных пользователей это просто их имя пользователя, но если у них есть псевдоним, специфичный для гильдии, он возвращается.
        """
        return ctx.author.display_name

    @commands.command()
    async def join(self, ctx: Context):
        """ Присоединение в голосовой в чат

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
        """
        name = await self.__get_username(ctx)
        voice_client: VoiceClient = ctx.voice_client
        if not await self.__check_access(ctx):
            return
        if isinstance(voice_client, VoiceClient) and voice_client.is_connected():
            await ctx.send(f"{name} я уже подключен, в глазки долбишься ⁉")
            return
        channel = ctx.author.voice.channel
        await channel.connect()

    @commands.command()
    async def disconnect(self, ctx: Context):
        """ Отключение из голосового в чат

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
        """
        name = await self.__get_username(ctx)
        voice_client: VoiceClient = ctx.voice_client
        if not await self.__check_access(ctx):
            return
        if voice_client is None:
            await ctx.send(f"{name} я уже отключен, в глазки долбишься ⁉")
            return
        await voice_client.disconnect()

    @commands.command()
    async def play(self, ctx: Context, url: str):
        """ Запуск youtube клипа по ссылке

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
            url (str): Ссылка на youtube клип
        """
        name = await self.__get_username(ctx)
        voice_client: VoiceClient = ctx.voice_client
        if not await self.__check_access(ctx):
            return
        if voice_client is None:
            await ctx.send(f'{name} будь добр напиши !join ⁉')
            return
        ctx.voice_client.stop()
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTIONS = {'format': "bestaudio"}
        vc = ctx.voice_client
        try:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                vc.play(source)
                await ctx.send('Сейчас играет - ' + info.get('title'))
                await self.__playlist(ctx)
        except DownloadError:
            await ctx.send(f'{name} ты не передал сыллку ⁉')

    @commands.command()
    async def add_song(self, ctx: Context, url: str):
        """ Добавление youtube клипа в очередь

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
            url (str): Ссылка на youtube клип
        """
        name = await self.__get_username(ctx)
        voice_client: VoiceClient = ctx.voice_client
        if not await self.__check_access(ctx):
            return
        if voice_client is None:
            await ctx.send(f'{name} будь добр напиши !join ⁉')
            return
        self.song_list.append(url)

    @commands.command()
    async def pause(self, ctx: Context):
        """ Приостановить youtube клип

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
        """
        name = await self.__get_username(ctx)
        voice_client: VoiceClient = ctx.voice_client
        if not await self.__check_access(ctx):
            return
        if voice_client is None:
            await ctx.send(f'{name} будь добр напиши !join ⁉')
            return
        if not voice_client.is_playing():
            await ctx.send(f"{name} я сейчас не играю музыку ⁉")
            return
        voice_client.pause()
        await ctx.send(f"{name} поставил паузу ⏸")

    @commands.command()
    async def resume(self, ctx: Context):
        """ Возобновить youtube клип

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
        """
        name = await self.__get_username(ctx)
        voice_client: VoiceClient = ctx.voice_client
        if not await self.__check_access(ctx):
            return
        if voice_client is None:
            await ctx.send(f'{name} будь добр напиши !join ⁉')
            return
        if not voice_client.is_paused():
            await ctx.send(f"{name} ты сначала поставь на паузу, а потом меня вызывай ⁉")
            return
        voice_client.resume()
        await ctx.send(f"{name} продолжил песню ⏯")

    @commands.command()
    async def skip(self, ctx: Context):
        """ Пропустить youtube клип

        Args:
            ctx (Context): Представляет контекст, в котором вызывается команда.
        """
        name = await self.__get_username(ctx)
        voice_client: VoiceClient = ctx.voice_client
        if not await self.__check_access(ctx):
            return
        if voice_client is None:
            await ctx.send(f'{name} будь добр напиши !join ⁉')
            return
        if isinstance(voice_client, VoiceClient) and not voice_client.is_playing():
            await ctx.send(f'{name} песен больше не осталось, может скипнуть тебя ⁉')
            return
        voice_client.stop()
        await ctx.send(f"{name} скипнул песню 💨")


def setup(bot):
    bot.add_cog(MusicCog(bot))
