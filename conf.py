from rule import Rule

class BotConfig(object):
    def __init__(self):
        # Default values
        self.server = None
        self.port = 6667
        self.channel = None
        self.nick = None
        self.password = None
        self.rules = []

    # _scan_X: scan line from index for the extent of X
    # Returns the token
    # Example: scan_variable("abc %(def)", 4) returns "%(def)"
    def _scan_variable(self, line, index):
        assert index < len(line) - 1
        assert line[index] == '%'
        assert line[index+1] == '('
        r_index = line.index(')', index+2)
        return line[index : r_index+1]

    def _scan_keyword(self, line, index):
        token = ''
        while index < len(line) and ((line[index] >= 'a' and line[index] <= 'z')
                                  or (line[index] >= 'A' and line[index] <= 'Z')
                                  or line[index] in '_'):
            token += line[index]
            index += 1
        return token

    def _scan_string(self, line, index):
        assert index < len(line)
        assert line[index] == '"'
        r_index = line.index('"', index+1)
        return line[index : r_index + 1]

    def _scan_numeral(self, line, index):
        token = ''
        while index < len(line) and line[index] in '0123456789.':
            token += line[index]
            index += 1
        return token

    def tokenize(self, line):
        tokens = []

        index = 0
        while index < len(line):
            if line[index] in ' \t':
                index += 1
            elif line[index] in ',=':
                tokens.append(line[index])
                index += 1
            elif line[index] == '%':
                token = self._scan_variable(line, index)
                tokens.append(token)
                index += len(token)
            elif line[index] == '"':
                token = self._scan_string(line, index)
                tokens.append(token)
                index += len(token)
            elif line[index] in '0123456789.':
                token = self._scan_numeral(line, index)
                tokens.append(token)
                index += len(token)
            else:
                token = self._scan_keyword(line, index)
                tokens.append(token)
                index += len(token)
        return tokens

    def parseFile(self, filename):
        with open(filename) as fin:
            lines = fin.read().splitlines()
        rule_tokens = []
        for line in lines:
            tokens = self.tokenize(line)
            if len(tokens) > 2 and tokens[1] == '=':
                assert len(tokens) == 3
                assert tokens[2][0] == '"'
                assert tokens[2][-1] == '"'
                assert tokens[0] in (
                    'server',
                    'nick',
                    'password',
                    'channel',
                    )
                setattr(self, tokens[0], tokens[2][1:-1])
                # Special case to split out port
                if tokens[0] == 'server':
                    s = self.server.split(':',1)
                    self.server = s[0]
                    if len(s) == 2:
                        try:
                            self.port = int(s[1])
                        except ValueError:
                            assert False, "Bad port"
            elif len(tokens) > 0 and tokens[0] == 'rule':
                if len(rule_tokens) > 0:
                    self.rules.append(Rule(rule_tokens))
                rule_tokens = [tokens]
            elif len(tokens) > 0:
                rule_tokens.append(tokens)
        if len(rule_tokens) > 0:
            self.rules.append(Rule(rule_tokens))
