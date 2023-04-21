# -*- coding: utf-8 -*

from __future__ import absolute_import, unicode_literals
import pywikibot
from pywikibot import pagegenerators, Bot
import os
import requests
from datetime import datetime
import pandas as pd


class SeroBOT(Bot):
    """BOT que revierte desde ORES"""

    def __init__(self, generator, site=None, **kwargs):
        self.available_options.update({
            'gf': 0.085,
            'dm': 0.970,
            'wiki': 'eswiki'
        })

        super(SeroBOT, self).__init__(**kwargs)
        self.generator = generator
        self.site = site
        if self.site.logged_in() is False:
            self.site.login()
        self.wiki = "{}{}".format(self.site.lang, str(
            self.site.family).replace('pedia', ''))

    def run(self):
        for page in filter(lambda x: self.valid(x), self.generator):
            try:
                revision, buena_fe, danina, resultado = self.checkORES(page)
            except Exception as exp:
                print(exp)
                continue
            data = [revision, buena_fe, danina, resultado,
                    page._rcinfo.get('user'), page.title(), datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())]
            self.do_log(data)
            if resultado is True:
                self.do_reverse(page)
                if (self.site.family.name == 'wikipedia' and self.site.lang == 'es'):
                    self.check_user(page._rcinfo.get('user'), page.title())
                    self.check_pagina(page.title())

    def valid(self, page):
        """
        Determina si un cambio es válido para poder invocar el endpoint de ORES
        Selecciona
        * solo las ediciones,
        * el usuario no es bot
        * espacios de nombres 0 y 104 (principal y anexo)
        * el usuario no soy yo mismo (SeroBOT)

        @param page: página a chequear
        @return true
        """
        return page._rcinfo.get('type') == 'edit' and page._rcinfo.get('bot') is False and page._rcinfo.get('namespace') in [0, 104] and page._rcinfo.get('user') != self.site.username()

    def checkORES(self, page):
        """
        Chequea la página en ORES y determina si la probabilidad de reversa es verdadera o no
        """
        headers = {
            'User-Agent': 'SeroBOT - an ORES counter vandalism tool'
        }
        wiki = self.wiki
        revision = page._rcinfo.get('revision')
        ores = str(revision.get('new'))
        url = 'https://ores.wikimedia.org/v3/scores/{0}/{1}'.format(wiki, ores)
        r = requests.get(url=url, headers=headers)
        data = r.json()
        try:
            goodfaith = data.get(wiki).get('scores').get(ores).get('goodfaith')
            damaging = data.get(wiki).get('scores').get(ores).get('damaging')
            buena_fe = goodfaith.get('score').get('probability').get('true')
            danina = damaging.get('score').get('probability').get('true')
            return (ores, buena_fe, danina, True if buena_fe < self.available_options.get('gf') or danina > self.available_options.get('dm') else False)
        except:
            pywikibot.exception()

    def do_log(self, data):
        """
        Escribe y limpia el log, si el tiempo es superior a 6 horas
        """
        wiki = self.wiki
        general = "{0}/log/{1}-general.log".format(os.path.dirname(
            os.path.realpath(__file__)), wiki)
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(
            os.path.realpath(__file__)), wiki)
        with open(general, encoding='utf-8', mode='a+') as archivo:
            archivo.write(u'\t'.join(map(lambda x: str(x), data)) + u'\n')
        if data[3] is True:
            with open(positivo, encoding='utf-8', mode='a+') as archivo:
                archivo.write(u'\t'.join(map(lambda x: str(x), data)) + u'\n')

    def check_user(self, usuario, pagina):
        wiki = self.wiki
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(
            os.path.realpath(__file__)), wiki)
        df_reversas = pd.read_csv(positivo, header=None, delimiter='\t')
        user = df_reversas[4] == usuario
        page = df_reversas[5] == pagina
        past = (int(datetime.utcnow().timestamp())
                - df_reversas[7]) < (60 * 60 * 4)  # 4 horas
        rows = df_reversas[user & page & past]
        User = pywikibot.User(self.site, usuario)
        if (len(rows) == 2 and User.isAnonymous() is False):
            talk = pywikibot.Page(self.site, title=usuario, ns=3)
            talk.text += u"\n{{sust:Aviso prueba2|" + pagina + "}} ~~~~"
            talk.save(
                summary=u'Aviso de pruebas a usuario tras reversiones consecutivas')
            return
        rows = df_reversas[user & past]
        if (len(rows) == 4):
            vec = pywikibot.Page(self.site, title='Vandalismo en curso', ns=4)
            tpl = "\n" + u'{{subst:'
            tpl += 'ReportevandalismoIP' if User.isAnonymous() else 'Reportevandalismo'
            tpl += u'|1=' + usuario
            tpl += u'|2=Reversiones: ' + \
                (', '.join(
                    map(lambda x: u'[[Special:Diff/' + str(x) + '|diff: ' + str(x) + ']]', rows[0])))
            tpl += u'}}'
            vec.text += "\n" + tpl
            try:
                vec.save(summary=u'Reportando al usuario [[Special:Contributions/'
                         + usuario + '|' + usuario + ']] por posibles ediciones vándalicas')
            except:
                pass
        return

    def check_pagina(self, pagina):
        wiki = self.wiki
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(
            os.path.realpath(__file__)), wiki)
        df_reversas = pd.read_csv(positivo, header=None, delimiter='\t')
        page = df_reversas[5] == pagina
        past = (int(datetime.utcnow().timestamp())
                - df_reversas[7]) < (60 * 60 * 4)  # 4 horas
        users = df_reversas[page & past][4].nunique()

        rows = df_reversas[page & past]
        if (len(rows) < 6 or users < 2):
            return

        tabp = pywikibot.Page(
            self.site, title='Tablón de anuncios de los bibliotecarios/Portal/Archivo/Protección de artículos/Actual', ns=4)
        if (tabp.get().find('{{{{a|{0}}}}}'.format(pagina)) != -1):
            return
        tpl = "\n" + '{{{{subst:Usuario:SeroBOT/TABP|pagina={0}|firma=~~~~}}}}'.format(
            pagina)
        tabp.text += "\n" + tpl
        try:
            tabp.save(
                summary=u'Solicitando protección de [[{0}]] por reversiones consecutivas'.format(pagina))
        except:
            pass
        return

    def do_reverse(self, page):
        try:
            history = list(page.revisions(total=2))
            if len(history) <= 1:
                return False
            print('reversa de ' + page.title())
            self.site.rollbackpage(page)
        except:
            pass


def main(*args):
    """
    Procesa los parámetros desde la línea de comandos

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    opts = {}
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg.startswith('-gf:'):
            opts['gf'] = float(arg[4:])
        elif arg.startswith('-dm:'):
            opts['dm'] = float(arg[4:])
        elif arg.startswith('-wiki:'):
            opts['wiki'] = arg[6:]

    site = pywikibot.Site()
    if 'wiki' in opts and opts['wiki'] != 'eswiki':
        lang = opts['wiki'][0:2]
        family = opts['wiki'][2:]
        site = pywikibot.Site(lang, family)

    bot = SeroBOT(pagegenerators.LiveRCPageGenerator(site),
                  site=site, **opts)
    bot.run()


if __name__ == '__main__':
    main()
