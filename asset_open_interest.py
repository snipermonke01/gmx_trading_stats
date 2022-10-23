#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 12:46:41 2022

@author: snipermonke01
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
from PIL import Image

from utils import TelegramManager


class AssetOpenInterest(TelegramManager):

    def __init__(self):

        super().__init__()

        self.subgraph_url = {"arbitrum": "https://api.thegraph.com/subgraphs/name/nissoh/gmx-arbitrum",
                             "avax": "https://api.thegraph.com/subgraphs/name/nissoh/gmx-avalanche"}
        self.arbitrum_token_index = {"eth": '"0x82af49447d8a07e3bd95bd0d56f35241523fbab1"',
                                     "btc": '"0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f"',
                                     "link": '"0xf97f4df75117a78c1a5a0dbb814af92458539fb4"',
                                     "uni": '"0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0"'}
        self.avax_token_index = {"wbtc": '"0x50b7545627a5162f82a992c33b87adc75187b218"',
                                 "btc": '"0x152b9d0fdc40c096757f570a51e494bd4b943e50"',
                                 "eth": '"0x49d5c2bdffac6ce2bfdb6640f4f80f226bc10bab"',
                                 "avax": '"0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7"'}
        self.arbitrum_token_list = ["eth", "btc", "link", "uni"]
        self.avax_token_list = ["wbtc", "btc", "eth", "avax"]

    def start_app(self):

        raw_oi_collat = self._get_all_token_open_interest()

        processed_open_interest = self._process_open_interest(raw_oi_collat)
        processed_collat = self._process_collat(raw_oi_collat)

        self._make_oi_barchart(processed_open_interest)
        files = self._prepare_oi_plot()
        self.telegram_bot_image(files)

        self._make_avg_levarage_bar_chart(processed_collat)
        files = self._prepare_avg_collat_plot()
        self.telegram_bot_image(files)

    @staticmethod
    def _make_avg_levarage_bar_chart(processed_collat):

        x_raw = [label.replace("_", " ")
                 for label in list(processed_collat.keys())]
        x_raw = [label.replace("short", "S")
                 for label in x_raw]
        x_raw = [label.replace("long", "L")
                 for label in x_raw]
        x = [label.replace(" avg lev", "") for label in x_raw]
        colors = ['g', 'r', 'g', 'r', 'g', 'r', 'g', 'r', 'g',
                  'r', 'g', 'r', 'g', 'r', 'g', 'r']

        plt.barh(x, processed_collat.values(), color=colors)
        # plt.xticks(rotation=90)
        plt.xlabel("Avg lev (x)")
        plt.title("GMX Average Leverage Used")
        red_patch = mpatches.Patch(color='red', label='Short Positions')
        green_patch = mpatches.Patch(color='green', label='Long Positions')
        plt.legend(handles=[red_patch, green_patch],
                   loc='upper right',
                   prop={'size': 10},
                   framealpha=1.0,
                   fancybox=True,
                   shadow=True)
        plt.savefig('collat_image.png',
                    dpi=600,
                    bbox_inches='tight')
        plt.close()

    @staticmethod
    def _make_oi_barchart(processed_open_interest):
        plt.style.use('dark_background')

        plt.barh(1.7,
                 processed_open_interest['total_btc_long'],
                 align='center',
                 color='green',
                 edgecolor='black')
        plt.barh(1.7,
                 -processed_open_interest['total_btc_short'],
                 align='center',
                 color='red',
                 edgecolor='black')
        plt.barh(2.55,
                 processed_open_interest['total_eth_long'],
                 align='center',
                 color='green',
                 edgecolor='black')
        plt.barh(2.55,
                 -processed_open_interest['total_eth_short'],
                 align='center',
                 color='red',
                 edgecolor='black')

        plt.barh(0.85,
                 processed_open_interest['total_alt_long'],
                 align='center',
                 color='green',
                 edgecolor='black')
        plt.barh(0.85,
                 -processed_open_interest['total_alt_short'],
                 align='center',
                 color='red',
                 edgecolor='black')

        locs = np.array([-50000000, -40000000, -30000000, -20000000,
                         -10000000, 0, 10000000, 20000000, 30000000,
                         40000000, 50000000])

        labels = ["${}m".format((abs(label)/1000000).astype(int))
                  for label in locs]
        plt.xticks(locs, labels)
        plt.yticks([0.85, 1.7, 2.55], ['Alts', 'BTC', 'ETH'])

        plt.title('GMX Open Interest By Asset')
        plt.savefig('asset_image.png',
                    dpi=600,
                    bbox_inches='tight')
        plt.close()

    def _process_open_interest(self, raw_open_interest):

        total_eth_long = raw_open_interest['eth_long_arbitrum'] + \
            raw_open_interest['eth_long_avax']
        total_eth_short = raw_open_interest['eth_short_arbitrum'] + \
            raw_open_interest['eth_short_avax']
        total_btc_long = raw_open_interest['btc_long_arbitrum'] + \
            raw_open_interest['btc_long_avax'] + \
            raw_open_interest['wbtc_long_avax']
        total_btc_short = raw_open_interest['btc_short_arbitrum'] + \
            raw_open_interest['btc_short_avax'] + \
            raw_open_interest['wbtc_short_avax']
        total_alt_long = raw_open_interest['link_long_arbitrum'] + \
            raw_open_interest['uni_long_arbitrum'] + \
            raw_open_interest['avax_long_avax']
        total_alt_short = raw_open_interest['link_short_arbitrum'] + \
            raw_open_interest['uni_short_arbitrum'] + \
            raw_open_interest['avax_short_avax']

        return {"total_eth_long": total_eth_long,
                "total_eth_short": total_eth_short,
                "total_btc_long": total_btc_long,
                "total_btc_short": total_btc_short,
                "total_alt_long": total_alt_long,
                "total_alt_short": total_alt_short}

    def _process_collat(self, raw_oi_collat):

        avax_long_avg_lev = raw_oi_collat['avax_long_avax'] / \
            raw_oi_collat['avax_long_collat_avax']
        avax_short_avg_lev = raw_oi_collat['avax_short_avax'] / \
            raw_oi_collat['avax_short_collat_avax']
        btc_arb_long_avg_lev = raw_oi_collat['btc_long_arbitrum'] / \
            raw_oi_collat['btc_long_collat_arbitrum']
        btc_arb_short_avg_lev = raw_oi_collat['btc_short_arbitrum'] / \
            raw_oi_collat['btc_long_collat_arbitrum']
        btc_avax_long_avg_lev = raw_oi_collat['btc_long_avax'] / \
            raw_oi_collat['btc_long_collat_avax']
        btc_avax_short_avg_lev = raw_oi_collat['btc_short_avax'] / \
            raw_oi_collat['btc_short_collat_avax']
        wbtc_avax_long_avg_lev = raw_oi_collat['wbtc_long_avax'] / \
            raw_oi_collat['wbtc_long_collat_avax']
        wbtc_avax_short_avg_lev = raw_oi_collat['wbtc_short_avax'] / \
            raw_oi_collat['wbtc_short_collat_avax']
        eth_arb_long_avg_lev = raw_oi_collat['eth_long_arbitrum'] / \
            raw_oi_collat['eth_long_collat_arbitrum']
        eth_arb_short_avg_lev = raw_oi_collat['eth_short_arbitrum'] / \
            raw_oi_collat['eth_short_collat_arbitrum']
        eth_avax_long_avg_lev = raw_oi_collat['eth_long_avax'] / \
            raw_oi_collat['eth_long_collat_avax']
        eth_avax_short_avg_lev = raw_oi_collat['eth_short_avax'] / \
            raw_oi_collat['eth_short_collat_avax']
        link_arb_long_avg_lev = raw_oi_collat['link_long_arbitrum'] / \
            raw_oi_collat['link_long_collat_arbitrum']
        link_arb_short_avg_lev = raw_oi_collat['link_short_arbitrum'] / \
            raw_oi_collat['link_short_collat_arbitrum']
        uni_arb_long_avg_lev = raw_oi_collat['uni_long_arbitrum'] / \
            raw_oi_collat['uni_long_collat_arbitrum']
        uni_arb_short_avg_lev = raw_oi_collat['uni_short_arbitrum'] / \
            raw_oi_collat['uni_short_collat_arbitrum']

        average_leverage = {"avax_long_avg_lev": avax_long_avg_lev,
                            "avax_short_avg_lev": avax_short_avg_lev,
                            "btc_arb_long_avg_lev": btc_arb_long_avg_lev,
                            "btc_arb_short_avg_lev": btc_arb_short_avg_lev,
                            "btc_avax_long_avg_lev": btc_avax_long_avg_lev,
                            "btc_avax_short_avg_lev": btc_avax_short_avg_lev,
                            "wbtc_avax_long_avg_lev": wbtc_avax_long_avg_lev,
                            "wbtc_avax_short_avg_lev": wbtc_avax_short_avg_lev,
                            "eth_arb_long_avg_lev": eth_arb_long_avg_lev,
                            "eth_arb_short_avg_lev": eth_arb_short_avg_lev,
                            "eth_avax_long_avg_lev": eth_avax_long_avg_lev,
                            "eth_avax_short_avg_lev": eth_avax_short_avg_lev,
                            "link_arb_long_avg_lev": link_arb_long_avg_lev,
                            "link_arb_short_avg_lev": link_arb_short_avg_lev,
                            "uni_arb_long_avg_lev": uni_arb_long_avg_lev,
                            "uni_arb_short_avg_lev": uni_arb_short_avg_lev}

        return average_leverage

    def _get_all_token_open_interest(self):

        open_interest = {}

        for token_name in self.arbitrum_token_list:
            print("Fetching Arbitrum {} positions..".format(token_name))
            token_open_interest_dict = self._get_token_long_shot_oi("arbitrum",
                                                                    token_name)
            open_interest.update(token_open_interest_dict)

        for token_name in self.avax_token_list:
            print("Fetching AVAX {} positions..".format(token_name))
            token_open_interest_dict = self._get_token_long_shot_oi("avax",
                                                                    token_name)
            open_interest.update(token_open_interest_dict)

        return open_interest

    def _get_token_long_shot_oi(self, chain, token_name):

        long_subgraph_query = self._build_subgraph_query(chain,
                                                         token_name,
                                                         is_long=True)
        long_response = self._make_query(chain,
                                         long_subgraph_query)
        long_oi, long_collat, long_pnl = self._process_subgraph_response(
            long_response)

        short_subgraph_query = self._build_subgraph_query(chain,
                                                          token_name,
                                                          is_short=True)
        short_response = self._make_query(chain,
                                          short_subgraph_query)
        short_oi, short_collat, short_pnl = self._process_subgraph_response(
            short_response)

        return {"{}_long_{}".format(token_name, chain): long_oi,
                "{}_short_{}".format(token_name, chain): short_oi,
                "{}_long_collat_{}".format(token_name, chain): long_collat,
                "{}_short_collat_{}".format(token_name, chain): short_collat,
                "{}_long_pnl_{}".format(token_name, chain): long_pnl,
                "{}_short_pnl_{}".format(token_name, chain): short_pnl}

    @staticmethod
    def _process_subgraph_response(raw_response):

        response_df = pd.DataFrame(raw_response['data']['trades'])
        print(len(response_df))
        asset_oi = response_df['size'].astype(
            float).sum()/1000000000000000000000000000000

        collateral = response_df['collateral'].astype(
            float).sum()/1000000000000000000000000000000

        pnl = response_df['realisedPnl'].astype(
            float).sum()/1000000000000000000000000000000

        return asset_oi, collateral, pnl

    def _build_subgraph_query(self,
                              chain,
                              token_name: str,
                              is_long: bool = False,
                              is_short: bool = False,
                              grab_extra: bool = False):

        if chain == 'arbitrum':

            token_index = self.arbitrum_token_index[token_name]
        elif chain == 'avax':
            token_index = self.avax_token_index[token_name]

        if is_long:
            position_type = 'true'
        elif is_short:
            position_type = 'false'
        else:
            raise Exception("Please select either is_short or is_long!")

        query = """{trades(first: 1000, where:{status: "open",
                        isLong: """+position_type+""",
                        indexToken: """ + token_index+"""}) {
                        isLong
                        account
                        status
                        indexToken
                        size
                        collateral
                        realisedPnl
                        key
                      }
                    }"""

        if grab_extra:
            query = """{trades(first: 1000, skip: 1000, where:{status: "open",
                            isLong: """+position_type+""",
                            indexToken: """ + token_index+"""}) {
                            isLong
                            account
                            status
                            indexToken
                            size
                            collateral
                            realisedPnl
                            key
                          }
                        }"""

        return query

    def _make_query(self, chain, query):

        url = self.subgraph_url[chain]

        response = requests.post(url,
                                 json={'query': query}).json()

        return response

    @staticmethod
    def _prepare_oi_plot():
        img = Image.open('asset_image.png')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return {"photo": img_bytes}

    @staticmethod
    def _prepare_avg_collat_plot():
        img = Image.open('collat_image.png')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return {"photo": img_bytes}
