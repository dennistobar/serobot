# -*- coding: utf-8 -*

import pandas as pd
import os

class estimador():

    def __init__(self, archivo, dir=os.path.realpath(__file__)):
        self.archivo = dir+'/'+archivo
        if os.path.isfile(self.archivo) == False:
            return False
        self.df = pd.read_csv(archivo, header=None, delimiter='\t')

    def check_user(self, user, page, max_time=60*60*4):
        df_user = self.df[4] == user
        df_page = self.df[5] == page
        df_past = (int(datetime.utcnow().timestamp()) - self.df[7]) < (max_time)
        return  df[df_user & df_page & df_past]

    def estimate_user(self, user):
        df_user = self.df[4] == user
        return self.df[user][1].min()
