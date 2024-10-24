import polars as pl
import pandas as pd
import numpy
import seaborn as sns

def significant_features(pca_data, scree_filename='scree.pdf', plot_dpi=300,
                         sigline=True, bar_filename='_significant_features.pdf'):
    '''
    Determines PCs that contribute to at least 90% of explained variance and
    which features weigh heavily on each PC.
    Parameters:
        pca_data: a Polars or Pandas data frame
        scree_filename: (default 'scree.pdf') filename of the scree plot
        plot_dpi: (default 300) DPI of plots
        sigline: (default True) whether you want a line specifying cutoff value
        bar_filename: (default '_significant_features.pdf') filename of the barplots
    Returns:
        A CSV file containing significant PCs and their loadings, a CSV file
        containing significance by feature, a scree plot, and bar plots of
        significance of features.
    '''
    if type(pca_data) is pd.core.frame.DataFrame:
        pca_data = pl.from_pandas(pca_data)
        is_polars = False
    elif type(pca_data) is pl.dataframe.frame.DataFrame:
        is_polars = True
    else:
        raise TypeError('Data must be in a Polars or Pandas Data Frame :(')
        
    # make a data frame for the scree plot; create new column converting to percent
    scree_plot_df = (
        pca_data
        .filter(pl.col('Index') == 'explained variance ratio')
        .select(pl.nth(range(1, pca_data.width)))
        .transpose(include_header=True,
                   header_name='PC',
                   column_names=['explained variance'])
    ).with_columns((pl.col('explained variance').cast(pl.Float32) * 100 ).alias('explained variance percent'))

    # determine the number of PCs that account for >= 90% of explained variance
    variance_ratio = 0
    pc_index = 0
    significant_pcs = []
    while variance_ratio < 90 and pc_index <= scree_plot_df.height:
        variance_ratio += scree_plot_df[pc_index, 2]
        significant_pcs.append(scree_plot_df[pc_index, 0])
        pc_index += 1

    # create scree plot
    scree_plot = sns.barplot(
        x='PC',
        y='explained variance percent',
        data=scree_plot_df
    )

    # highlight PCs that account for >= 90% of explained variance
    scree_plot.axvspan(pc_index - 0.5,
                       -1,
                       alpha=0.1,
                       color='red',
                       zorder=0,
                       label=f'{variance_ratio:.2f}% of Explained\nVariance'
    )
    scree_plot.axvline(pc_index - 0.5,
                       color='darkred',
                       linestyle='--'
    )
    
    # set limits, legend, labels, etc.
    scree_plot.set_xlim(-1)
    scree_plot.legend()
    scree_plot.set_xlabel('Principal Component')
    scree_plot.set_ylabel('Explained Variance (%)')
    scree_plot.figure.tight_layout()

    # save plot to disk and clear seaborn
    scree_plot.figure.savefig(scree_filename, dpi=plot_dpi)
    scree_plot.figure.clf()

    # create data frame to determine significant features
    sig_feature_df = (
        pl.DataFrame(pca_data['Index'])
        # filter out explained variance and explained variance ratios
        # basically to isolate the PCA scores themselves
        .filter(
            (pl.col('Index') != 'explained variance')
            & (pl.col('Index') != 'explained variance ratio')
        )
    )

    # iterate over each significant PC
    for pc in significant_pcs:
        feature_subset = (
            pca_data
            # select only index column and singular pc column
            .select(pl.col('Index', pc))
            # filter out explained variances to isolate loadings
            .filter(
               (pl.col('Index') != 'explained variance')
               & (pl.col('Index') != 'explained variance ratio')
            )
        ).sort(pc, descending=True)  # sort from highest to lowest values

        # determine significance cutoff
        # basically the average loading score
        cutoff = (1 / feature_subset.height) ** (1/2)

        # record significant or not significant if absolute value of loading
        # is greater than the cutoff value
        feature_subset = (
            feature_subset
            .with_columns(
                Significance = pl.when(pl.col(pc) >= cutoff)
                .then(pl.lit('Significant'))
                .when(pl.col(pc) <= -(cutoff))
                .then(pl.lit('Significant'))
                .otherwise(pl.lit('Not Significant'))
            )
        )

        # create barplot of variables and significance
        feature_bar = sns.barplot(
            x=pc,
            y='Index',
            data=feature_subset,
            hue='Significance'
        )
        # if significance line is specified (default)
        # add lines at cutoff point
        if sigline:
            feature_bar.axvline(cutoff,
                                color='firebrick',
                                linestyle='--',
                                linewidth=1)
        if sigline and feature_subset[pc].min() < 0:
            feature_bar.axvline(-(cutoff),
                                color='firebrick',
                                linestyle='--',
                                linewidth=1)
            feature_bar.axvline(0,
                                color='black',
                                linewidth=1)
        
        # legend stuff
        feature_bar.legend(title='Significance')
        sns.move_legend(feature_bar, "upper left", bbox_to_anchor=(1, 1))

        # title/axis label stuff
        feature_bar.set_title(f'Principal Component {pc[2:]}',
                     fontsize=16)
        feature_bar.set_xlabel('Loading')
        feature_bar.set_ylabel('Feature')

        # make sure things don't overlap
        feature_bar.figure.tight_layout()

        # save barplot to disk
        feature_bar.figure.savefig(f'{pc}{bar_filename}', dpi=plot_dpi)
        feature_bar.figure.clf()

        # record significance of features to data frame
        sig_feature_df = sig_feature_df.with_columns(feature_subset['Significance'].alias(f'{pc} Significance'))

    # write output data frames to disk
    sig_feature_df.write_csv('significance_of_features.csv')
    significant_pcs = (pca_data
    .filter(
        (pl.col('Index') != 'explained variance')
        & (pl.col('Index') != 'explained variance ratio')
    )
    .select(pl.col('Index').alias('Feature'), pl.col(significant_pcs))
    )
    significant_pcs.write_csv('significant_pcs.csv')

    # print messages
    print('Written to disk as significant_pcs.csv', significant_pcs)
    print('\nWritten to disk as significance_of_features.csv', sig_feature_df)
    print(f'\nLoadings with an absolute value >= {cutoff} are significant.\n',
    'Significance was determined according to the following formula:\n',
    '    (1 / num_variables) ** (1/2)')

    # write notes to a text file
    with open('significant_features_notes.txt', 'w') as file:
        file.writelines('Significant features are features which have an '
                        + f'absolute value >= {cutoff}.\nThe cutoff value was '
                        + 'calculated according to the following formula:'
                        + f'\n\t(1 / {pca_data.height - 1}) ** (1/2)'
                        )

    return significant_pcs