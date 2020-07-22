# -*- coding: utf-8 -*-
#
#        H A P P Y    H A C K I N G !
#              _____               ______
#     ____====  ]OO|_n_n__][.      |    |
#    [________]_|__|________)<     |YANG|
#     oo    oo  'oo OOOO-| oo\\_   ~o~~o~
# +--+--+--+--+--+--+--+--+--+--+--+--+--+
#               Jianing Yang @  8 Feb, 2018
#
from tornado_battery import disable_tornado_logging_options  # noqa
from tornado_battery.command import CommandMixin
from tornado_battery.controller import JSONController
from tornado_battery.route import route
from tornado_battery.redis import register_redis_options, with_redis, connect_redis
from tornado.options import options
from tornado.gen import sleep as async_sleep
from tornado.web import Application as WebApplication

import logging

LOG = logging.getLogger("tornado.application")


@route("/api/v1/counter")
class AddController(JSONController):

    @with_redis(name="subordinate")
    async def get(self, redis):
        name = self.get_argument("name", "default")
        value = await redis.execute('get', 'counter-%s' % name)
        self.reply(name=name, counter=value)

    @with_redis(name="main")
    async def post(self, redis):
        name = self.get_argument("name", "default")
        await redis.execute('incr', 'counter-%s' % name)
        value = await self.nested_redis_incr(name)
        self.reply(name=name, counter=value)

    @with_redis(name="main")
    async def nested_redis_incr(self, name, redis):
        await redis.execute('incr', 'counter-%s' % name)
        value = await self.nested_redis_check(name)
        return value

    @with_redis(name="subordinate")
    async def nested_redis_check(self, name, redis):
        value = await redis.execute('get', 'counter-%s' % name)
        await async_sleep(5)
        LOG.info(f'inner value = {value}')
        return value


class GreetingServer(CommandMixin):

    def setup(self):
        register_redis_options("main", "redis://localhost/0")
        register_redis_options("subordinate", "redis://localhost/0")

    def before_run(self, io_loop):
        io_loop.run_sync(connect_redis("main"))
        io_loop.run_sync(connect_redis("subordinate"))

        app = WebApplication(route.get_routes(), autoreload=options.debug)
        app.listen(8000, "0.0.0.0")
        LOG.info("server started.")


start_server = GreetingServer()
