import os

import altair as alt
import numpy as np
import pandas as pd
import panel as pn
import param
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
N_IMG = int(os.getenv('N_IMG', "10"))

emoji_json = requests.get(url="https://api.github.com/emojis").json()
img_source = pd.DataFrame({"name": list(emoji_json.keys()), "url": list(emoji_json.values()),
                           'x': np.random.uniform(-50, 50, len(emoji_json)),
                           'y': np.random.uniform(-50, 50, len(emoji_json))})


class ReactiveDashboard(param.Parameterized):
    title = pn.pane.Markdown("# Example Dashboard")
    n_images = param.Integer(label='Number of images', default=200, bounds=(100, 500))

    @pn.depends('n_images')
    def plot(self):
        img_subset = img_source.sample(self.n_images)
        ch = alt.Chart(img_subset, width=500, height=500).mark_image(width=40, height=40).encode(
            x='x',
            y='y',
            url='url'
        )
        return ch

    def panel(self):
        return pn.Column(self.param, self.plot)


res = ReactiveDashboard(name="").panel()
pn.serve({"panel_main": res, "health": pn.pane.Markdown("Healthcheck")},address='0.0.0.0',
         port=int(os.getenv('POST', 5006)),
         websocket_origin="paneltest.herokuapp.com")
