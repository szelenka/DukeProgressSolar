# Solar Conversion Calculator

This is a simple project to obtain historical data from Duke Progress Energy for your property, then calculate how large of a Solar Array you'd need for your home to make it worth your while.

## Install steps
Pre-req to get plotly to render offline in Jupyter-lab, see [FigureWidget in Jupyter Lab](https://plot.ly/python/jupyter-lab-tools/) for more details:
```
conda install nodejs
jupyter labextension install @jupyter-widgets/jupyterlab-manager 
jupyter labextension install plotlywidget
```

```
pip install -r requirements.txt
jupyter lab
```

## Running
1. Download the latest [ChromeDriver](https://chromedriver.storage.googleapis.com/index.html?path=2.42/) and extract to the (./drivers)[./drivers] folder. This is needed for selenium to automate gathering data from the website(s).
1. Populate the credentials in the [./credentialsconfig.env](./credentials/config.env) file.
1. Then open up the [./Widgets.ipynb](./Widgets.ipynb) notebook.
