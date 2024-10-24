import polars as pl
import pandas as pd
import numpy as np
import math
from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import seaborn as sns

def allo(character, bl_mean, x, X):
    y = character.log10().to_numpy()

    # perform linear regression
    model = LinearRegression()
    model.fit(X, y)
    slope = model.coef_

    # calculate Xadj 
    adj = pl.Series(
        y - slope * (x - bl_mean)
    ).alias(character.name)
    return adj

def allom(data, filename='allom_output.csv'):
    '''
    Performs allometric size correction on morphometric characters.
    Parameters:
        data: a Polars or Pandas data frame
        filename: (default 'allom_output.csv') sets file name of CSV file
            containing allometric corrections.
    Returns:
        A CSV file containing allometric size corrections.
    '''

    # check to see if input data are in correct format
    if type(data) is pd.core.frame.DataFrame:
        data = pl.from_pandas(data)
    elif type(data) is pl.dataframe.frame.DataFrame:
        pass
    else:
        raise TypeError('Data must be in a Polars or Pandas Data Frame :(')

    # list of species
    species_unique = list(
        data[:, 0].unique()
    )

    # iterate over species for allometric correction
    allom_df = pl.DataFrame()
    for species in species_unique:
        # subset data to current species
        subset = (
            data
            .filter(pl.col(data.columns[0]) == species)
        )

        # calculate log10 of body length and log10 of mean of body length
        bl = subset[:, 1].log10()
        bl_mean = math.log10(subset[:, 1].mean())
        x = bl.to_numpy()     # convert to numpy array for Xadj calculation
        X = x.reshape(-1, 1)  # reshaped for linear regression

        # iterate over character columns, perform allometric correction
        allom_df = allom_df.vstack(
            subset.select(
                pl.nth(range(2, subset.width))
                .map_batches(lambda character: allo(character, bl_mean, x, X))
            )
            .insert_column(0, subset[:, 0])          # species names
            .insert_column(1, subset[:, 1].log10())  # log10 of body length
        )

    # write allometric correction table to disk
    allom_df.write_csv(filename)
    print(f'Allometric Correction:\n - saved to disk as {filename}\n')
    return allom_df
    
def morph_pca(allom_df, allom_filename='allom_output.csv',
            plot_filename='pca_plot.pdf', plot_dpi=300, plot_kde=True,
            plot_kde_levels=2, plot_title=None,
            plot_palette='colorblind', plot_style='ticks'):
    '''
    Performs allometric size correction and principal component analysis on
    morphometric characters.
    Parameters:
        data: a Polars or Pandas data frame
        allom_filename: (default 'allom_output.csv') sets file name of CSV file
            containing allometric corrections.
        plot_filename: (default: 'pca.pdf')
        plot_filetype: (default 'pdf') sets the output filetype of the PCA plot.
        plot_dpi: (default 300) sets the DPI of the PCA plot.
        plot_kde: (default True) adds KDE to PCA plot if True.
        plot_kde_levels: (default 2) sets KDE levels of PCA plot.
        plot_title: (default None) adds title to the PCA plot.
        plot_palette: (default 'colorblind') sets color palette of PCA plot.
        plot_style: (default 'ticks') sets matplotlib style of plot.
    Returns:
        A CSV file containing allometric size corrections, a CSV file
        containing PCA results, and a PCA plot.
    '''
    
    # scale for PCA
    scaler = StandardScaler()
    scaled_allom = scaler.fit_transform(allom_df[:, 1:])

    # perform PCA with 10 components
    chars_pca = PCA(n_components=10)
    pcs = chars_pca.fit_transform(scaled_allom)

    # write out column names for 10 PCs
    pca_schema = ['PC1', 'PC2', 'PC3', 'PC4', 'PC5', 'PC6', 'PC7', 'PC8', 'PC9',
                  'PC10']

    # make data frame of explained variance row-wise
    variance = pl.from_numpy(chars_pca.explained_variance_.reshape(1, -1), schema=pca_schema)
    # make data frame of explained variance ratio row-wise
    variance_ratio = pl.DataFrame(chars_pca.explained_variance_ratio_.reshape(1, -1), schema=pca_schema)
    # make data frame of loadings row-wise
    loadings = pl.from_numpy(chars_pca.components_.T, schema=pca_schema)
    # create index column with statistic/character names
    index_col = (
        pl.concat([
            pl.Series('Index', ['explained variance', 'explained variance ratio']),
            pl.Series('Index', allom_df[:, 1:].columns)
        ])
    )

    # create final PCA output table and write to disk
    pca_out_df = (
        variance
        .vstack(variance_ratio)
        .vstack(loadings)
    ).insert_column(0, index_col)
    pca_out_df.write_csv('pca_output.csv')
    print('\nPCA Results:\n - saved to disk as pca_output.csv\n', pca_out_df)

    # make data frame for PCA plot including species column
    pca_df = pl.DataFrame(
        data=pcs,
        schema=pca_schema
    ).insert_column(0, allom_df[:, 0].alias('Species'))

    # calculate variance of PC1 and PC2 as a percentage
    pc1_variance = chars_pca.explained_variance_ratio_[0] * 100
    pc2_variance = chars_pca.explained_variance_ratio_[1] * 100

    # graph PCA
    sns.set_theme(style=plot_style, palette=plot_palette)
    # add KDE to scatter plot only if kde=True
    if plot_kde:
        sns.kdeplot(
            x='PC1',
            y='PC2',
            data=pca_df,
            hue='Species',
            fill=True,
            levels=plot_kde_levels,
            alpha=0.1
        )    
        sns.kdeplot(
            x='PC1',
            y='PC2',
            data=pca_df,
            hue='Species',
            levels=plot_kde_levels,
            alpha=0.5
        )

    # generate scatterplot, colored by species
    pca_plot = sns.scatterplot(
        x='PC1',
        y='PC2',
        data=pca_df,
        hue='Species'
    )

    # move legend to top etc.
    sns.move_legend(
        pca_plot, "lower center",
        bbox_to_anchor=(.5, 1),
        ncol=4,
        title=None,
        frameon=False,
    )

    # add title if a plot title is specified
    if plot_title:
        pca_plot.figure.suptitle(plot_title)
    
    # change axis labels to display variance of each PC
    pca_plot.set_xlabel(f'PC1 ({pc1_variance:.2f}%)')
    pca_plot.set_ylabel(f'PC2 ({pc2_variance:.2f}%)')
    pca_plot.figure.tight_layout()  # keeps everything from overlapping

    # show plot and save plot to disk
    pca_plot.figure.savefig(plot_filename, dpi=plot_dpi)
    print(f'\nPCA Plot:\n - saved to disk as {plot_filename}')
    pca_plot.figure.show()
    pca_plot.figure.clf()

    return pca_out_df