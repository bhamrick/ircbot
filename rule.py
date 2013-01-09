# A rule consists of several actions
# Each action will return True or False
# A False response will terminate the rule
# For simplicity, actions with side effects
# such as say will have the side effects occur
# immediately, even if the rule terminates early later

import re
import time

class Action(object):
    def __init__(self, action_type, params):
        self.action_type = action_type
        self.params = params
        # Used for global rate limiting
        self.last_time = 0

    def _expand_string(self, s, env):
        # Replace %(var) with the value of var in s
        # Replaces %% with %
        # Also unwraps the string from quotes if they exist
        index = 0
        result = ""
        while index < len(s):
            if s[index] == '%':
                if s[index + 1] == '%':
                    result += '%'
                    index += 2
                elif s[index + 1] == '(':
                    r_index = s.index(')', index+2)
                    var_name = s[index+2:r_index]
                    result += str(env.get(var_name,""))
                    index = r_index + 1
                else:
                    assert False, "Bad string expansion"
            else:
                result += s[index]
                index += 1
        if result[0] == '"' and result[-1] == '"':
            result = result[1:-1]
        return result

    def _match(self, connection, env):
        # match string, regex
        params = self.params
        assert len(params) == 2
        s = self._expand_string(params[0], env)
        r = self._expand_string(params[1], env)
        print "Attempting to match %r with %r" % (s, r)
        match = re.search(r, s)
        if match:
            env.update(match.groupdict())
            return True
        else:
            return False

    def _say(self, connection, env):
        # say message
        # send a message to the channel from which
        # the event came, which is in env["channel"]
        params = self.params
        msg = self._expand_string(params[0], env)
        chan = env["channel"]
        connection.privmsg(chan, msg)
        print "Saying %r to %r" % (msg, chan)
        return True

    def _require_mode(self, connection, env):
        # Checks that the sender has the specified modes
        # Example: require_mode +o requires that the user is an op
        # require_mode -o requires that they are not an op
        # require_mode -ov requires that they are neither op nor voiced
        params = self.params
        print "Checking for modes", params[0]
        ch = env["channel"]
        user = env["user"]
        require_in = True
        for c in params[0]:
            if c == '+':
                require_in = True
            elif c == '-':
                require_in = False
            elif c == 'o':
                if require_in != (user in env["ch_ops"]):
                    return False
            elif c == 'v':
                if require_in != (user in env["ch_voiced"]):
                    return False
        return True

    def _global_rate_limit(self, connection, env):
        # Refuse to execute more than once in params[0] seconds
        params = self.params
        delta = float(params[0])
        curtime = time.time()
        if curtime - self.last_time > delta:
            self.last_time = curtime
            return True
        return False

    def _set(self, connection, env):
        params = self.params
        varname = params[0]
        if varname[0] == '%' and varname[1] == '(' and varname[-1] == ')':
            varname = varname[2:-1]
        value = self._expand_string(params[1], env)
        env[varname] = value
        return True

    def execute(self, connection, env):
        func = getattr(self, "_" + self.action_type, None)
        return func and func(connection, env)

class Rule(object):
    def __init__(self):
        self.name = ""
        self.actions = []

    def __init__(self, tokenized_lines):
        self.name = ""
        self.actions = []
        for line in tokenized_lines:
            if len(line) > 0:
                if line[0] == 'rule':
                    self.name = ' '.join(line[1:])
                else:
                    action = Action(line[0], [token for token in line[1:] if token != ','])
                    self.actions.append(action)

    def run(self, connection, env):
        for action in self.actions:
            if not action.execute(connection, env):
                return False
        print "Matched rule", self.name
        return True
