# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class IfolderRu(SimpleHoster):
    __name    = "IfolderRu"
    __type    = "hoster"
    __version = "0.39"

    __pattern = r'http://(?:www\.)?(?:ifolder\.ru|rusfolder\.(?:com|net|ru))/(?:files/)?(?P<ID>\d+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Ifolder.ru hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    SIZE_REPLACEMENTS = [(u'Кб', 'KB'), (u'Мб', 'MB'), (u'Гб', 'GB')]

    NAME_PATTERN    = ur'(?:<div><span>)?Название:(?:</span>)? <b>(?P<N>[^<]+)</b><(?:/div|br)>'
    SIZE_PATTERN    = ur'(?:<div><span>)?Размер:(?:</span>)? <b>(?P<S>[^<]+)</b><(?:/div|br)>'
    OFFLINE_PATTERN = ur'<p>Файл номер <b>[^<]*</b> (не найден|удален) !!!</p>'

    SESSION_ID_PATTERN = r'<a href=(http://ints\.(?:rusfolder\.com|ifolder\.ru)/ints/sponsor/\?bi=\d*&session=([^&]+)&u=[^>]+)>'
    INTS_SESSION_PATTERN = r'\(\'ints_session\'\);\s*if\(tag\)\{tag\.value = "([^"]+)";\}'
    HIDDEN_INPUT_PATTERN = r'var v = .*?name=\'(.+?)\' value=\'1\''

    LINK_FREE_PATTERN = r'<a id="download_file_href" href="([^"]+)"'

    WRONG_CAPTCHA_PATTERN = ur'<font color=Red>неверный код,<br>введите еще раз</font><br>'


    def setup(self):
        self.resumeDownload = self.multiDL = bool(self.account)
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        self.html = self.load("http://rusfolder.com/%s" % self.info['pattern']['ID'], decode=True)
        self.getFileInfo()

        url = re.search(r"location\.href = '(http://ints\..*?=)'", self.html).group(1)
        self.html = self.load(url, decode=True)

        url, session_id = re.search(self.SESSION_ID_PATTERN, self.html).groups()
        self.html = self.load(url, decode=True)

        url = "http://ints.rusfolder.com/ints/frame/?session=%s" % session_id
        self.html = self.load(url)

        self.wait(31, False)

        captcha_url = "http://ints.rusfolder.com/random/images/?session=%s" % session_id
        for _i in xrange(5):
            self.html = self.load(url)
            action, inputs = self.parseHtmlForm('ID="Form1"')
            inputs['ints_session'] = re.search(self.INTS_SESSION_PATTERN, self.html).group(1)
            inputs[re.search(self.HIDDEN_INPUT_PATTERN, self.html).group(1)] = '1'
            inputs['confirmed_number'] = self.decryptCaptcha(captcha_url, cookies=True)
            inputs['action'] = '1'
            self.logDebug(inputs)

            self.html = self.load(url, decode=True, post=inputs)
            if self.WRONG_CAPTCHA_PATTERN in self.html:
                self.invalidCaptcha()
            else:
                break
        else:
            self.fail(_("Invalid captcha"))

        self.link = re.search(self.LINK_PATTERN, self.html).group(1)
