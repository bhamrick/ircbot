#!/usr/bin/env python
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

from conf import BotConfig
from rule import Rule

DEBUG = True

class MusselBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667, password=None, rules=[]):
        print "Initializing"
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel
        self.rules = rules
        self.env = {}

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + '_')

    def log_event(self,e):
        if DEBUG:
            print e.type
            print e.source
            print e.target
            print e.arguments
            print ""

    def on_welcome(self, c, e):
        self.log_event(e)
        c.execute_delayed(1, c.join, (self.channel,))

    def on_namreply(self, c, e):
        self.log_event(e)

    def on_endofnames(self, c, e):
        self.log_event(e)

    def on_join(self, c, e):
        self.log_event(e)

    def on_pubmsg(self, c, e):
        self.log_event(e)
        self.env["user"] = e.source.split("!", 1)[0]
        self.env["channel"] = e.target
        self.env["message"] = e.arguments[0]
        self.env["ch_names"] = self.channels[e.target].userdict
        self.env["ch_ops"] = self.channels[e.target].operdict
        self.env["ch_voiced"] = self.channels[e.target].voiceddict
        for rule in self.rules:
            rule.run(c, self.env)

    def on_privmsg(self, c, e):
        self.log_event(e)

    def on_pubnotice(self, c, e):
        self.log_event(e)

    def on_privnotice(self, c, e):
        self.log_event(e)

    def on_error(self, c, e):
        self.log_event(e)

    def on_ping(self, c, e):
        self.log_event(e)

    def on_pong(self, c, e):
        self.log_event(e)

    def on_mode(self, c, e):
        self.log_event(e)

    def on_disconnect(self, c, e):
        self.log_event(e)

def main():
    import sys
    if len(sys.argv) < 2:
        print "Usage: bot <config file>"

    conf = BotConfig()
    conf.parseFile(sys.argv[1])

    bot = MusselBot(conf.channel,
                    conf.nick,
                    conf.server,
                    conf.port,
                    conf.password,
                    conf.rules)
    bot.start()

if __name__ == "__main__":
    main()
