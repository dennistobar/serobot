# -*- coding: utf-8 -*

import os
from datetime import datetime
from functools import lru_cache

import pandas as pd
import requests

import pywikibot
from pywikibot import Bot, User, pagegenerators

USER_AGENT = 'SeroBOT - an ORES/revertrisk-language-agnostic counter vandalism tool'

class SeroBOT(Bot):

    """BOT que revierte desde ORES."""

    def __init__(self, generator, site, **kwargs):
        self.available_options.update({
            'dm': 0.954,
            'wikifamily': 'eswiki'
        })
        super(SeroBOT, self).__init__(**kwargs)

        self.generator = generator
        self.site = site
        if not self.site.logged_in():
            self.site.login()
        self.wiki = "{}{}".format(self.site.lang, str(self.site.family).replace('pedia', ''))

    @property
    def log_dir(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log')

    def _log_path(self, suffix):
        return os.path.join(self.log_dir, f"{self.wiki}-{suffix}.log")

    def run(self):
        for page in filter(self.valid, self.generator):
            try:
                if self.site.family == 'wikibooks':
                    revision, buena_fe, danina, resultado, algorithm = self.check_damaging(page)
                else:
                    revision, buena_fe, danina, resultado, algorithm = self.check_risk(page)
            except Exception as exp:
                print(exp)
                continue

            if revision is None:
                continue

            data = [revision, buena_fe, danina, resultado, page._rcinfo.get('user'), page.title(),
                    datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp()), algorithm]
            self.do_log(data)
            if resultado:
                self.do_reverse(page, page._rcinfo.get('user'))
                if self.site.family.name == 'wikipedia' and self.site.lang == 'es':
                    self.check_user(page._rcinfo.get('user'), page.title())
                    self.check_pagina(page.title())

    def valid(self, page):
        """Check if we need to check the page from the LiveRCGenerator.

        @param page: Page to check
        @returns: bool
        """
        username = page._rcinfo.get('user')

        return (
            # Solo lo que sea edicion
            page._rcinfo.get('type') == 'edit' and
            # que no sea bot
            not page._rcinfo.get('bot') and
            # que esté en el espacio principal o anexo
            page._rcinfo.get('namespace') in {0, 104} and
            # que no sea yo mismo
            page._rcinfo.get('user') != self.site.username() and
            # que no sea una reversa (tag de reversa, los RV manual no los considera)
            'mw-rollback' not in list(page.revisions(total=1))[0]['tags'] and
            # el usuario no es sysop (o bibliotecario en Wikipedia en español)
            'sysop' not in self.retrieve_user(username).groups()
        )

    @lru_cache(maxsize=500)
    def retrieve_user(self, username):
        """Retrieve an user from the username. It uses this function to cache the results."""
        return User(self.site, username)

    def check_risk(self, page):
        """Send a request to Wikimedia API to check the revert-risk of the page."""
        headers = {'User-Agent': USER_AGENT}
        revision = page._rcinfo.get('revision')
        revision_check = revision.get('new')
        url = 'https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict'

        try:
            data = requests.post(url=url, headers=headers, json={
                                 'rev_id': revision_check, 'lang': self.site.lang}).json()
        except requests.RequestException as e:
            print(f'Error in API request: {e}')
            # Handle the error or consider returning a default value
            return None, None, None, None, None

        if 'output' in data and 'probabilities' in data['output']:
            return revision_check, data['output']['probabilities']['false'], data['output']['probabilities']['true'], \
                data['output']['probabilities']['true'] > self.getOption('dm'), 'revertrisk-language-agnostic'
        else:
            print('Unexpected API response format')
            # Handle the unexpected format or consider returning a default value
            return None, None, None, None, None

    def check_damaging(self, page):
        """Send a request to Wikimedia API to check the revert-risk of the page."""
        headers = {'User-Agent': USER_AGENT}
        revision = page._rcinfo.get('revision')
        revision_check = revision.get('new')
        url = 'https://api.wikimedia.org/service/lw/inference/v1/models/{}{}-damaging:predict'.format(self.site.lang, self.site.family)

        try:
            data = requests.post(url=url, headers=headers, json={
                                 'rev_id': revision_check, 'lang': self.site.lang}).json()
        except requests.RequestException as e:
            print(f'Error in API request: {e}')
            # Handle the error or consider returning a default value
            return None, None, None, None, None

        if self.wiki in data and 'scores' in data[self.wiki]:
            scores = data[self.wiki]['scores'][revision_check]['damaging']['score']
            return revision_check, scores['probability']['false'], scores['probability']['true'], \
                scores['probability']['true'] > self.getOption('dm'), 'revscoring damaging'
        else:
            print('Unexpected API response format')
            # Handle the unexpected format or consider returning a default value
            return None, None, None, None, None

    def do_log(self, data):
        wiki = self.wiki
        print(wiki)
        general = self._log_path('general')
        positivo = self._log_path('positivo')

        with open(general, encoding='utf-8', mode='a+') as archivo:
            archivo.write('\t'.join(map(str, data)) + '\n')

        if data[3]:
            with open(positivo, encoding='utf-8', mode='a+') as archivo:
                archivo.write('\t'.join(map(str, data)) + '\n')

    def check_user(self, user, page):
        """Check for consecutive reversions by the same user."""
        positive_log_path = self._log_path('positivo')
        df_reversas = pd.read_csv(
            positive_log_path, header=None, delimiter='\t')
        user_reversions = df_reversas[(
            df_reversas[4] == user) & (df_reversas[5] == page)]

        # Handle two consecutive reversions by a registered user
        if len(user_reversions) == 2:
            if not pywikibot.User(self.site, user).isAnonymous():
                talk_page = pywikibot.Page(self.site, title=user, ns=3)
                talk_page.text += "\n{{subst:Aviso prueba2|" + page + "}} ~~~~"
                summary = 'Aviso de pruebas a usuario tras reversiones consecutivas'
                try:
                    talk_page.save(summary=summary)
                except pywikibot.Error as e:
                    print(f'Error saving talk page: {e}')
                return

        # Handle four consecutive reversions by any user
        if len(user_reversions) == 4:
            vandalism_page = pywikibot.Page(
                self.site, title='Vandalismo en curso', ns=4)
            template = "\n" + '{{subst:'
            template += 'ReportevandalismoIP' if pywikibot.User(
                self.site, user).isAnonymous() else 'Reportevandalismo'
            template += '|1=' + user
            template += '|2=Reversiones: ' + (', '.join(
                map(lambda x: '[[Special:Diff/' + str(x) + '|diff: ' + str(x) + ']]', user_reversions[0])))
            template += '}}'
            vandalism_page.text += "\n" + template
            summary = 'Reportando al usuario [[Special:Contributions/' + \
                user + '|' + user + ']] por posibles ediciones vándalicas'
            try:
                vandalism_page.save(summary=summary)
            except pywikibot.Error as e:
                print(f"Error saving vandalism page: {e}")
        return

    def check_pagina(self, pagina):
        positivo = self._log_path('positivo')
        df_reversas = pd.read_csv(positivo, header=None, delimiter='\t')
        page = df_reversas[5] == pagina
        past = (int(datetime.utcnow().timestamp()) -
                df_reversas[7]) < (60 * 60 * 4)  # 4 horas
        users = df_reversas[page & past][4].nunique()
        rows = df_reversas[page & past]
        if len(rows) < 6 or users < 2:
            return

        tabp = pywikibot.Page(
            self.site, title='Tablón de anuncios de los bibliotecarios/Portal/Archivo/Protección de artículos/Actual',
            ns=4)
        if tabp.get().find('{{{{a|{0}}}}}'.format(pagina)) != -1:
            return
        tpl = "\n" + \
            '{{{{subst:Usuario:SeroBOT/TABP|pagina={0}|firma=~~~~}}}}'.format(
                pagina)
        tabp.text += "\n" + tpl
        try:
            tabp.save(
                summary='Solicitando protección de [[{0}]] por reversiones consecutivas'.format(pagina))
        except pywikibot.Error as e:
            print(f'Error saving tablon: {e}')
        return

    def do_reverse(self, page, user):
        try:
            print('reversa de ' + page.title())

            self.site.rollbackpage(page, user=user, markbot=False)
        except Exception as exp:
            print(exp)
            pass


def main(*args):
    opts = {}
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg.startswith('-dm:'):
            opts['dm'] = float(arg[4:])
        elif arg.startswith('-wikifamily:'):
            opts['wikifamily'] = arg[12:]

    site = pywikibot.Site()
    if 'wikifamily' in opts and opts['wikifamily'] != 'eswiki':
        lang = opts['wikifamily'][0:2]
        family = opts['wikifamily'][2:]
        site = pywikibot.Site(lang, family)

    bot = SeroBOT(pagegenerators.LiveRCPageGenerator(site), site=site, **opts)
    bot.run()


if __name__ == '__main__':
    main()
