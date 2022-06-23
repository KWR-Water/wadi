from collections import UserList

class StringList(UserList):
    def replace_strings(self, r_dict):
        if not isinstance(r_dict, dict):
            raise TypeError("Argument 'r_dict' must be of type dict")
        try:
            for key, value in r_dict.items():
                self.data = [s.replace(key, value) for s in self.data]
        except:
            pass

s = StringList(['test', 'giller'])
s.replace_strings({'e': 'a', 'il': '3'})
print(s)