# -*- coding: utf-8 -*

from __future__ import absolute_import, unicode_literals
import pywikibot
from pywikibot import pagegenerators, Bot
import sys
import os
import requests
import time
from datetime import datetime
import pandas as pd


class SeroBOT(Bot):

    """BOT que revierte desde ORES"""

    def __init__(self, generator, site=None, **kwargs):
        self.availableOptions.update({
            'gf': 0.085,
            'dm': 0.970,
            'wiki': 'eswiki',
            'debug': False
        })
        """Constructor."""
        super(SeroBOT, self).__init__(**kwargs)
        self.generator = generator
        self.site = site
        if self.site.logged_in() == False:
            self.site.login()

    def run(self):
        for page in filter(lambda x: self.valid(x), self.generator):
            try:
                revision, buena_fe, danina, resultado = self.checkORES(page)
            except:
                continue
            data = [revision, buena_fe, danina, resultado,
                    page._rcinfo.get('user'), page.title(), datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())]
            if self.getOption('debug'):
                print (data)
            self.do_log(data)
            self.do_reverse(page) if resultado == True else False
            if (self.site.family.name == 'wikipedia' and self.site.lang == 'es'):
                self.check_user(page._rcinfo.get('user'), page.title()) if resultado == True else False
                self.check_pagina(page.title()) if resultado == True else False


    def valid(self, page):
        return page._rcinfo.get('type') == 'edit' and page._rcinfo.get('bot') == False and page._rcinfo.get('namespace') in [0, 104] and page._rcinfo.get('user') != self.site.username()

    def checkORES(self, page):
        headers = {
            'User-Agent': 'SeroBOT - an ORES counter vandalism tool'
        }
        wiki = self.getOption('wiki')
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
            return (ores, buena_fe, danina, True if buena_fe < self.getOption('gf') or danina > self.getOption('dm') else False)
        except:
            pywikibot.exception()

    def do_log(self, data):
        general = "{0}/log/{1}-general.log".format(os.path.dirname(os.path.realpath(__file__)), self.getOption('wiki'))
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(os.path.realpath(__file__)), self.getOption('wiki'))
        with open(general, encoding='utf-8', mode='a+') as archivo:
            archivo.write(u'\t'.join(map(lambda x: str(x), data)) + u'\n')
        if data[3] == True:
            with open(positivo, encoding='utf-8', mode='a+') as archivo:
                archivo.write(u'\t'.join(map(lambda x: str(x), data)) + u'\n')

    def check_user(self, usuario, pagina):
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(os.path.realpath(__file__)), self.getOption('wiki'))
        df_reversas = pd.read_csv(positivo, header=None, delimiter='\t')
        user = df_reversas[4] == usuario
        page = df_reversas[5] == pagina
        past = (int(datetime.utcnow().timestamp()) - df_reversas[7]) < (60*60*4) # 4 horas
        rows = df_reversas[user & page & past]
        User = pywikibot.User(self.site, usuario)
                if (len(rows) == 1):
            if self.getOption('debug'):
                print ('Avisando a ',usuario)
            talk = pywikibot.Page(self.site, title=usuario, ns=3)
            talk.text += u"\n{{sust:Aviso prueba1|"+ pagina +"}} ~~~~"
            talk.save(comment=u'Aviso de pruebas a usuario tras reversiones consecutivas')
            with open(os.path.dirname(os.path.realpath(__file__)) + '/log/discusiones.log', 'a+') as archivo:
                archivo.write('\t'.join(map(lambda x: str(x), [usuario, pagina, datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())])) + '\n')
            return
        if (len(rows) == 2):
            if self.getOption('debug'):
                print ('Avisando a ',usuario)
            talk = pywikibot.Page(self.site, title=usuario, ns=3)
            talk.text += u"\n{{sust:Aviso prueba2|"+ pagina +"}} ~~~~"
            talk.save(comment=u'Aviso de pruebas a usuario tras reversiones consecutivas')
            with open(os.path.dirname(os.path.realpath(__file__)) + '/log/discusiones.log', 'a+') as archivo:
                archivo.write('\t'.join(map(lambda x: str(x), [usuario, pagina, datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())])) + '\n')
            return
        rows = df_reversas[user & past]
               if (len(rows) == 3):
            if self.getOption('debug'):
                print ('Avisando a ',usuario)
            talk = pywikibot.Page(self.site, title=usuario, ns=3)
            talk.text += u"\n{{sust:Aviso prueba3|"+ pagina +"}} ~~~~"
            talk.save(comment=u'Aviso de pruebas a usuario tras reversiones consecutivas')
            with open(os.path.dirname(os.path.realpath(__file__)) + '/log/discusiones.log', 'a+') as archivo:
                archivo.write('\t'.join(map(lambda x: str(x), [usuario, pagina, datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())])) + '\n')
            return
               if (len(rows) == 4):
            if self.getOption('debug'):
                print ('Avisando a ',usuario)
            talk = pywikibot.Page(self.site, title=usuario, ns=3)
            talk.text += u"\n{{sust:Aviso prueba4|"+ pagina +"}} ~~~~"
            talk.save(comment=u'Aviso de pruebas a usuario tras reversiones consecutivas')
            with open(os.path.dirname(os.path.realpath(__file__)) + '/log/discusiones.log', 'a+') as archivo:
                archivo.write('\t'.join(map(lambda x: str(x), [usuario, pagina, datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())])) + '\n')
            return
        if (len(rows) == 5):
            if self.getOption('debug'):
                print ('VEC a ',usuario)
            with open(os.path.dirname(os.path.realpath(__file__)) + '/log/vec.log', 'a+') as archivo:
                archivo.write('\t'.join(map(lambda x: str(x), [usuario, datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())])) + '\n')

            vec = pywikibot.Page(self.site, title='Vandalismo en curso', ns=4)
            tpl = u'{{subst:'
            tpl += 'ReportevandalismoIP' if User.isAnonymous() else 'Reportevandalismo'
            tpl += u'|1='+usuario
            tpl += u'|2=Reversiones: '+(', '.join(map(lambda x: u'[[Special:Diff/'+str(x)+'|diff: '+str(x)+']]', rows[0])))
            tpl += u'}}'
            vec.text += "\n"+tpl
            try:
                vec.save(comment=u'Reportando al usuario [[Special:Contributions/'+usuario+'|'+usuario+']] por posibles reversiones vandálicas')
            except:
                pass
        return

    def check_pagina(self, pagina):
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(os.path.realpath(__file__)), self.getOption('wiki'))
        df_reversas = pd.read_csv(positivo, header=None, delimiter='\t')
        page = df_reversas[5] == pagina
        past = (int(datetime.utcnow().timestamp()) - df_reversas[7]) < (60*60*4) # 4 horas
        rows = df_reversas[page & past]
        if (len(rows) < 6):
            return
        if self.getOption('debug'):
            print ('Solicitud de protección de página ',pagina)

        tabp = pywikibot.Page(self.site, title='Tablón de anuncios de los bibliotecarios/Portal/Archivo/Protección de artículos/Actual', ns=4)
        if (tabp.get().find('{{{{a|{0}}}}}'.format(pagina)) != -1):
            return
        tpl = '{{{{subst:Usuario:SeroBOT/TABP|pagina={0}|firma=~~~~}}}}'.format(pagina)
        tabp.text += "\n"+tpl
        try:
            tabp.save(comment=u'Solicitando protección de {0} por reversiones consecutivas'.format(pagina))
        except:
            pass
        return

    def do_reverse(self, page):
        if self.getOption('debug'):
            print ('>> Reversion', page._rcinfo.get('user'), page.title())
        try:
            token = pywikibot.data.api.Request(site=self.site, parameters={
                                               'action': 'query', 'meta': 'tokens', 'type': 'rollback'}).submit()['query']['tokens']['rollbacktoken']

            parameters = {'action': 'rollback',
                          'title': page.title(),
                          'user': page._rcinfo.get('user'),
                          'token': token,
                          'markbot': True}

            pywikibot.data.api.Request(
                site=self.site, parameters=parameters).submit()
            return
        except Exception as e:
            print (u'No puedo revertir la página ', e)

        # page.text = page.getOldVersion(page._rcinfo.get('revision').get('old'))
        # page.save(comment=u'Revirtiendo página por vandalismo detectado por [[:mw:ORES|ORES]]')

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
        elif arg.startswith('--debug'):
            opts['debug'] = True

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
