# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class PremiumizeMe(MultiHook):
    __name    = "PremiumizeMe"
    __type    = "hook"
    __version = "0.17"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Premiumize.me hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Florian Franzen", "FlorianFranzen@gmail.com")]


    def getHosters(self):
        # Get account data
        user, data = self.account.selectAccount()

        # Get supported hosters list from premiumize.me using the
        # json API v1 (see https://secure.premiumize.me/?show=api)
        answer = self.getURL("https://api.premiumize.me/pm-api/v1.php",
                        get={'method': "hosterlist", 'params[login]': user, 'params[pass]': data['password']})
        data = json_loads(answer)

        # If account is not valid thera are no hosters available
        if data['status'] != 200:
            return []

        # Extract hosters from json file
        return data['result']['hosterlist']
