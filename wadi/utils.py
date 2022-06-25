from collections import UserList
import re

def check_arg(arg, valid_args):
    """
    """
    try:
        #idx = [s.find(arg.lower()) for s in valid_args].index(0)
        #return valid_args[idx]
        find = re.compile(rf"^{arg}", re.IGNORECASE)
        return [s for s in valid_args if find.match(s)][0]
    except (ValueError, IndexError) as e:
        raise ValueError(f"invalid argument: '{arg}' must be in {valid_args}")

def check_arg_list(arg_list, valid_args):
    """
    """

    if isinstance(arg_list, str):
        arg_list = [arg_list]

    return [check_arg(a, valid_args) for a in arg_list]

class RegexMapper(object):
    def __init__(self, *args, func=None):
        self.RE = self._dict2RE(*args)
        self.func = func

    @staticmethod
    def _dict2RE(*args):
        rv = r""
        for i, re_dict in enumerate (args):
            if not isinstance(re_dict, dict):
                raise TypeError(f"argument {re_dict} must be of type dict")
            if (i == 0):
                rv += r"^\s*"
            else:
                rv += r"|^\s*"
            for key, value in re_dict.items():
                rv += rf"(?P<{key}>{value[0]}){value[1]}"
                #rv = r"\s*".join([rv, value[0] + rf"?P<{key}>" + value[1:]])
            rv += r"\s*$"

        return rv

    def str(self, groupdict):
        return self.func(groupdict)

class StringList(UserList):
    def replace_strings(self, r_dict):
        if not isinstance(r_dict, dict):
            raise TypeError("Argument 'r_dict' must be of type dict")
        try:
            for key, value in r_dict.items():
                self.data = [s.replace(key, value) for s in self.data]
        except:
            pass

    def strip_parentheses(self):
        self.data = [re.sub('\(.*\)', '', s) for s in self.data]

    def tidy_strings(self):
        self.data = [s.lower() for s in self.data]
        self.data = [s.encode('ascii', 'ignore').decode('ascii') for s in self.data]
        self.data = [re.sub('[^0-9a-zA-Z\s]', '', s) for s in self.data]
