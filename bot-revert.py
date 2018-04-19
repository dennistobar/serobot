# -*- coding: utf-8 -*

from __future__ import absolute_import, unicode_literals
import pywikibot
from pywikibot import pagegenerators
import urllib, json, sys, os

if sys.version_info[0] < 3:
    print ('No podemos ejecutar el bot en versiones inferirores a 3')
    os._exit(0)

from urllib import request

def scores(revs):
    url = 'https://ores.wmflabs.org/v3/scores/eswiki/?models=goodfaith|damaging&revids='+('|').join(revs)
    retornar = {}
    with request.urlopen(url) as response:
        data = json.loads(response.read())
        for rev in revs:
            goodfaith = data.get('eswiki').get('scores').get(rev).get('goodfaith')
            damaging = data.get('eswiki').get('scores').get(rev).get('damaging')
            prediccion = goodfaith.get('score').get('prediction')
            probabilidad = goodfaith.get('score').get('probability').get('true')
            d_prediccion = damaging.get('score').get('prediction')
            d_probabilidad = damaging.get('score').get('probability').get('true')
            retornar[rev] = {'buena_fe': prediccion, 'prob': probabilidad, 'danina': d_prediccion, 'prob_d': d_probabilidad}
    return retornar

def score(rev):
    return scores([rev]).get(rev)

Site = pywikibot.Site()

if Site.logged_in() == False:
    Site.login()

for page in pagegenerators.LiveRCPageGenerator(site=Site):
    if page._rcinfo.get('type') == 'edit' and page._rcinfo.get('namespace') in [0, 100] and page._rcinfo.get('user') != Site.username():
        revision = page._rcinfo.get('revision')
        ores = score(str(revision.get('new')))
        print ('>' if ores.get('prob') < 0.095 else ' ', revision.get('new'), ores.get('prob'), ores.get('prob_d'), page.title(), page._rcinfo.get('user'))
        if ores.get('prob') < 0.095 or ores.get('prob_d') > 0.97 or (ores.get('prob') < 0.13 and ores.get('prob_d') > 0.90):
            old = page.text
            page.text = page.getOldVersion(revision.get('old'))
            pywikibot.showDiff(old, page.text)
            try:
                #page.save(u'BOT - Reversión de página ([[:mw:ORES|ORES]]: '+ str(ores.get('prob'))+')')

                token = pywikibot.data.api.Request(site=Site, parameters={'action': 'query', 'meta':'tokens', 'type': 'rollback'}).submit()['query']['tokens']['rollbacktoken']

                parameters={'action': 'rollback',
                           'title': page.title(),
                           'user': page._rcinfo.get('user'),
                           'token': token,
                           'markbot': True}

                pywikibot.data.api.Request(
                    site=Site, parameters=parameters).submit()

            except Exception as e:
                print (u'No puedo guardar la página')
