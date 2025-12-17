#TODO check predict real, it is declared twice
import sys
sys.path.append("..")

# Make model
import numpy as np
import pandas as pd


from sklearn import metrics
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, ConfusionMatrixDisplay, RocCurveDisplay

from sklearn.model_selection import train_test_split, GridSearchCV

from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer, TfidfTransformer

#from sklearn.linear_model import LogisticRegression

from sklearn.svm import LinearSVC, SVC
from sklearn.naive_bayes import MultinomialNB, ComplementNB, BernoulliNB
from sklearn.ensemble import RandomForestClassifier

from sklearn.pipeline import make_pipeline


from lime.lime_text import LimeTextExplainer
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score



# Plot model
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.lines as mlines




import seaborn as sns

# Save files
from file_management import check_save_file



def set_parameters(model_name):
    if model_name == 'random_forest':
        model = RandomForestClassifier(random_state=24)

        search_parameters = {
            'max_depth': [1000, 2000],  # Include None to consider no depth limitation
            'max_features': ['sqrt', 'log2'],  # Added 'log2' and None for all features
            'n_estimators': [100, 500],  # Added 1000 for more trees
        }

    elif model_name == 'BernoulliNB':
        model = BernoulliNB()

        search_parameters = {
            'alpha': [0.1, 1.0, 10],  # Added 0.1 for lower smoothing
            'binarize': [0.0, 0.5, 1.0],  # Added 1.0 as an additional threshold
            'fit_prior': [True, False],  # Added False to test the effect of ignoring prior probabilities
            'class_prior': [None, [0.3, 0.7], [0.2, 0.8], [0.5, 0.5]]  # Added [0.5, 0.5] for balanced priors
        }

    elif model_name == 'SVC':
        model = SVC(probability=True)

        search_parameters = {
            'kernel': ['rbf', 'linear'],  # Reduced to 'rbf' and 'linear'
            'C': [0.1, 1.0, 10.0],  # Reduced to three key regularization values
            'gamma': ['scale', 'auto'],  # Kept 'scale' and 'auto' for gamma
            'class_weight': [None, 'balanced']  # Simplified to explore weight balancing
        }


    elif model_name == 'MultinomialNB':
        model = MultinomialNB()

        search_parameters = {
            'alpha': [0.1, 1.0, 21.0],  # Added 0.1 for lower smoothing
            'fit_prior': [True, False],  # Added False to test the effect of ignoring prior probabilities
            'class_prior': [None, [0.2, 0.8], [0.5, 0.5], [0.3, 0.7]]  # Added [0.3, 0.7] for different imbalance
        }

    return model, search_parameters

#Test functions



def preprocess_data(data, columns, functions):
    # Remove stop words etc
    for column in columns:
        for func in functions:
            data.loc[:, column] = data.loc[:, column].map(func)
    return data

def load_and_preprocess_laser_data(filepath, sep, columns, functions):
    # Remove stop words on laser dataset
    laser_data = pd.read_csv(filepath, sep=sep)
    laser_data['Clasification'] = 1
    laser_data = preprocess_data(laser_data, columns, functions)
    return laser_data







def evaluate_model(y_test, y_pred):
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred)
    #print(f"Accuracy: {accuracy}")
    #print(f"Precision: {precision}")
    #print(f"Recall: {recall}")
    #print(f"F1 Score: {f1}")
    #print(f"AUC-ROC: {auc}")
    return accuracy, precision, recall, f1, auc


    
        
def prepare_data(values, classification, max_df):
    X_train, X_test, y_train, y_test = train_test_split(values,
                                                        classification,
                                                        random_state=0)
    pipeline = make_pipeline(CountVectorizer(max_df=max_df), TfidfTransformer())
    X_train_vectorized = pipeline.fit_transform(X_train)
    X_test_vectorized = pipeline.transform(X_test)
    return X_train_vectorized, X_test_vectorized, y_train, y_test, pipeline




def small_larg_coef(vect, model):
    # get the feature names as numpy array
    feature_names = np.array(vect.get_feature_names())

    # Sort the coefficients from the model
    sorted_coef_index = model.coef_[0].argsort()

    # Find the 10 smallest and 10 largest coefficients
    # The 10 largest coefficients are being indexed using [:-11:-1] 
    # so the list returned is in order of largest to smallest
    small_coef = feature_names[sorted_coef_index[:10]]
    large_coef = feature_names[sorted_coef_index[:-30:-1]]
    
    print('\nSmallest Coefs:\n{}'.format(small_coef))
    print('\nLargest Coefs: \n{}'.format(large_coef))
    
    return(small_coef, large_coef)

def get_test_predictions(model, vect, test):
    using_title = sum(model.predict(vect.transform(test.loc[:,'Title'])))
    using_abstract = sum(model.predict(vect.transform(test.loc[:,'Abstract'])))
    using_both = sum(model.predict(vect.transform(test.loc[:,'Title']+' '+test.loc[:,'Abstract'])))
    
    print('\nPredictions using titles on the model:', using_title)
    print('\nPredictions using abstracts on the model:', using_abstract)
    print('\nPredictions using both on the model:', using_both)
    
    return([using_title, using_abstract, using_both])



def train_model_logreg(X_train, X_test, y_train, y_test, test, filename, model=None):
    if not model:
        model = MultinomialNB()  # Default to MultinomialNB
    
    pipeline = make_pipeline(CountVectorizer(max_df=0.9), TfidfTransformer(), model)
    pipeline.fit(X_train, y_train)
    
    predictions = pipeline.predict(X_test)
    
    # Evaluate the model
    print('\nAUC: ', roc_auc_score(y_test, predictions))
    
    try:
        small_coef, large_coef = small_larg_coef(pipeline.named_steps['countvectorizer'], model)
    except AttributeError:
        print('model has no coef')

    predic_real = get_test_predictions(pipeline, test)
    
    check_save_file(model, 'finalized_model_' + filename + '.sav', 'Models')
    check_save_file(pipeline.named_steps['countvectorizer'], 'finalized_vector_' + filename + '.sav', 'Models')
    
    return pipeline, predictions, predic_real

# In[ ]:



def make_matriz_conf(y_test, predictions, model, vect, test):
    cm = metrics.confusion_matrix(y_test, predictions)
    auc = roc_auc_score(y_test, predictions)

    return(cm, auc)



def compare_cm(values, start=80,end = 90):

    ax = values.plot('True positive', 'True negative', kind='scatter',
                     s=50, color='darkslategray',
                    zorder=2)
    def annotate_df(row):  
        ax.annotate(row.name, row.values,
                    xytext=(10,-5), 
                    textcoords='offset points',
                    size=15)
    _ = values.apply(annotate_df, axis=1)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    plt.xlabel('True positives',fontsize=15,fontweight ='bold')
    plt.ylabel('True negatives',fontsize=15,fontweight ='bold')

    plt.plot([start, end], [start, end], '--', lw=2, c='gray', alpha=0.5)
    plt.fill_between([start, end], [start, end], end, lw=0,
                     color='red',alpha=0.1, zorder=1)
    plt.fill_between([start, end], [start, end], start, lw=0,
                     color='green',alpha=0.1,zorder=0)
    plt.show()
    
    
    
    
#### Plots


def plot_metrics(y_test, y_pred, model_name, model, X_test):
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title(f'Confusion Matrix - {model_name}')
    plt.show()

    # ROC Curve
    RocCurveDisplay.from_estimator(model, X_test, y_test)
    plt.title(f'ROC Curve - {model_name}')
    plt.show()

def plot_comparison(models, metric_values, metric_name):
    bar_width = 0.35
    index = np.arange(len(models))
    
    plt.bar(index, metric_values, bar_width)
    plt.xlabel('Models')
    plt.ylabel(metric_name)
    plt.title(f'Comparison of {metric_name} across Models')
    plt.xticks(index, models, rotation=45)
    plt.tight_layout()
    plt.show()

    

#########


    
def explain_with_lime(pipeline, model, X_test_raw=None, sample_index=None, target_names=['Non-met', 'Met Eng'], sample_data=None):
    explainer = LimeTextExplainer(class_names=target_names)
    if not sample_data:
        sample_data = X_test_raw.iloc[sample_index]

    def predict_fn(texts):
        transformed_texts = pipeline.transform(texts)
        return model.predict_proba(transformed_texts)
    
    exp = explainer.explain_instance(sample_data, predict_fn, num_features=6, top_labels=1)
    exp.show_in_notebook(text=sample_data)
    

def test_parameters(X_train_vectorized, y_train, model_name, search_parameters):
    grid_search = GridSearchCV(model_name, search_parameters, cv=5, n_jobs=-1)
    grid_search.fit(X_train_vectorized, y_train)
    print(f'Best hyperparameters for {model_name}: {grid_search.best_params_}')
    return grid_search.best_estimator_

def train_and_evaluate_model(X_test_vectorized, y_test, best_model, model_name, target_names, pipeline, X_test_raw, LIME = True):
    y_pred = best_model.predict(X_test_vectorized)
    accuracy, precision, recall, f1, auc = evaluate_model(y_test, y_pred)
    
    print(f'\n{model_name} - AUC: {auc}')
    #lime
    if hasattr(best_model, "predict_proba") and LIME:
        explain_with_lime(pipeline, best_model, X_test_raw, sample_index=2, target_names=target_names)
    elif LIME==True:
        print(f"{model_name} does not support predict_proba; skipping LIME explanation.")

    return accuracy, precision, recall, f1, auc, y_pred

def preprocess_data_split(values, classification, vectorizer=None, transformer=None, test_size=0.2, random_state=0):
    X_train, X_test, y_train, y_test = train_test_split(values, classification, test_size=test_size, random_state=random_state)
    
    # Build the pipeline based on provided components
    pipeline_steps = []
    fitted_vectorizer = None
    fitted_transformer = None
    
    if vectorizer:
        fitted_vectorizer = vectorizer.fit(X_train)  # Fit the vectorizer
        X_train_vectorized = fitted_vectorizer.transform(X_train)  # Vectorize the training data
        X_test_vectorized = fitted_vectorizer.transform(X_test)  # Vectorize the test data
        pipeline_steps.append(fitted_vectorizer)
    
    if transformer:
        fitted_transformer = transformer.fit(X_train_vectorized)  # Fit the transformer on the vectorized data
        X_train_vectorized = fitted_transformer.transform(X_train_vectorized)  # Transform the training data
        X_test_vectorized = fitted_transformer.transform(X_test_vectorized)  # Transform the test data
        pipeline_steps.append(fitted_transformer)
    
    pipeline = make_pipeline(*pipeline_steps) if pipeline_steps else None
    
    return X_train, X_test, X_train_vectorized, X_test_vectorized, y_train, y_test, pipeline, fitted_vectorizer, fitted_transformer

def evaluate_model(y_test, y_pred):
    return (
        accuracy_score(y_test, y_pred),
        precision_score(y_test, y_pred),
        recall_score(y_test, y_pred),
        f1_score(y_test, y_pred),
        roc_auc_score(y_test, y_pred),
    )

def calculate_confusion_stats(y_test, y_pred):
    cm = confusion_matrix(y_test, y_pred)
    tp, fn, fp, tn = cm.ravel()
    true_positive_rate = (tp * 100) / (tp + fn)
    true_negative_rate = (tn * 100) / (tn + fp)
    return true_positive_rate, true_negative_rate


def gather_confusion_stats(model_names, y_preds, y_test,aucs, model_files, vectorizers, transformers):
    results = {'Model': [], 'Model_file':[],
               'True Positive (%)': [], 'True Negative (%)': [],'AUC':[],
              'Vectorizer':[],'Transformer':[]}
    for model_name, y_pred,auc, model_file, vect,transf in zip(model_names, y_preds,aucs,model_files, vectorizers,transformers):
        tp_rate, tn_rate = calculate_confusion_stats(y_test, y_pred)
        results['Model'].append(model_name)
        results['True Positive (%)'].append(tp_rate)
        results['True Negative (%)'].append(tn_rate)
        results['AUC'].append(auc)
        results['Model_file'].append(model_file)
        results['Vectorizer'].append(vect)
        results['Transformer'].append(transf)

    return pd.DataFrame(results)



def execute_pipeline(values, classification, models_to_test, target_names, LIME=True):
    pipelines = [
        ("Vectorizer + Transformer", CountVectorizer(max_df=0.85), TfidfTransformer()),
        ("Vectorizer Only", CountVectorizer(max_df=0.85), None),
        ("Vec 2", TfidfVectorizer(), None),
        ("vec2 + transformer", TfidfVectorizer(), TfidfTransformer()),
    ]
    
    all_results = []
    best_models_dict = {}  # Dictionary to store best models by model_name

    for pipeline_name, vectorizer, transformer in pipelines:
        print(f'\nPipeline: {pipeline_name}')
        X_train, X_test, X_train_vectorized, X_test_vectorized, y_train, y_test, pipeline, fitted_vectorizer, fitted_transformer = preprocess_data_split(
            values, classification, vectorizer, transformer
        )

        model_names = []
        y_preds = []
        aucs = []
        model_files = []
        vectorizers = []
        transformers = []
        for model_name in models_to_test:
            print(f'\nTraining {model_name}...')
            best_model = test_parameters(X_train_vectorized, y_train, *set_parameters(model_name))
            metrics = train_and_evaluate_model(
                X_test_vectorized, y_test, best_model, model_name, target_names, pipeline, X_test, LIME
            )
            model_names.append(model_name)
            y_preds.append(metrics[-1])
            aucs.append(metrics[-2])
            model_files.append(best_model)
            vectorizers.append(fitted_vectorizer)
            transformers.append(fitted_transformer)
        # Capture the fitted vectorizer/transformer in the results
        results_df = gather_confusion_stats(model_names, y_preds, y_test, aucs, model_files,
                                           vectorizers,transformers)
        results_df['Pipeline'] = pipeline_name
        #results_df['Vectorizer_file'] = fitted_vectorizer  # Return the fitted vectorizer
        #results_df['Transformer_file'] = fitted_transformer  # Return the fitted transformer

        all_results.append(results_df)
    
    combined_results = pd.concat(all_results)
    #plot_dumbbell(combined_results, by_pipeline=True)
    
    return combined_results

def plot_dumbbell(df, by_pipeline=False):
    fig, ax = plt.subplots(figsize=(12, 8))
    size=150
    green = '#9FA838'
    red = '#AA3939'
    blue = '#2C4770'
    line_w = 3
    # Track the maximum values for vertical lines
    max_true_positive = df['True Positive (%)'].max()
    max_true_negative = df['True Negative (%)'].max()
    max_auc = df['AUC'].max() if 'AUC' in df.columns else None
    max_auc *=100
    if by_pipeline:
        pipelines = df['Pipeline'].unique()
        start_index = 0
        y_ticks = []
        y_labels = []

        for pipeline in pipelines:
            df_pipeline = df[df['Pipeline'] == pipeline].sort_values('True Positive (%)').reset_index(drop=True)
            end_index = start_index + len(df_pipeline) - 1
            
            for i, row in df_pipeline.iterrows():
                y_ticks.append(start_index + i)
                y_labels.append(f"{row['Model']} ({pipeline})")
                ax.plot([row['True Positive (%)'], row['True Negative (%)']], [start_index + i, start_index + i], color='gray', lw=line_w)
                ax.scatter(row['True Positive (%)'], start_index + i, color='#365E87', s=size, label=f'True Positive - {pipeline}' if i == 0 else "")
                ax.scatter(row['True Negative (%)'], start_index + i, color='#CE484B', s=size, label=f'True Negative - {pipeline}' if i == 0 else "")
                
                # Add red dot for AUC
                #if max_auc is not None:
                ax.scatter(row['AUC']*100, start_index + i, color=green, s=size, label=f'AUC - {pipeline}' if i == 0 else "")

                    
            start_index = end_index + 2  # Adding space between pipeline groups

        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels,fontsize=14)

    else:
        df_sorted = df.sort_values('True Positive (%)').reset_index(drop=True)
        y_ticks = range(len(df_sorted))
        y_labels = [f"{row['Model']}" for _, row in df_sorted.iterrows()]

        for i, row in df_sorted.iterrows():
            ax.plot([row['True Positive (%)'], row['True Negative (%)']], [i, i], color='gray', lw=2)
            ax.scatter(row['True Positive (%)'], i, color=blue, s=50, label='True Positive' if i == 0 else "")
            ax.scatter(row['True Negative (%)'], i, color=red, s=50, label='True Negative' if i == 0 else "")

            # Add red dot for AUC
            if max_auc is not None:
                ax.scatter(max_auc, i, color=green, s=80, marker='o', label='AUC' if i == 0 else "")

        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels,fontsize=14)

    ax.set_xlabel('Percentage')
    ax.set_title('True Positive vs. True Negative Rates by Model and Pipeline')

    # Add dashed vertical lines at the maximum values
    ax.axvline(x=max_true_positive, color=blue, linestyle='--', linewidth=1.5, label='Max True Positive')
    ax.axvline(x=max_true_negative, color=red, linestyle='--', linewidth=1.5, label='Max True Negative')

    if max_auc is not None:
        ax.axvline(x=max_auc, color=green, linestyle='--', linewidth=1.5, label='Max AUC')

    # Add legend
    ax.legend(handles=[
        mlines.Line2D([], [], color=blue, marker='o', linestyle='None', markersize=8, label='True Positive (%)'),
        mlines.Line2D([], [], color=red, marker='o', linestyle='None', markersize=8, label='True Negative (%)'),
        mlines.Line2D([], [], color=green, marker='o', linestyle='None', markersize=8, label='AUC'),
        mlines.Line2D([], [], color=blue, linestyle='--', linewidth=1.5, label='Max True Positive'),
        mlines.Line2D([], [], color=red, linestyle='--', linewidth=1.5, label='Max True Negative'),
        mlines.Line2D([], [], color=green, linestyle='--', linewidth=1.5, label='Max AUC')
    ])
    
    plt.show()

    
    
    ###



#Function to calculate the performance metric you want (accuracy, true positive rate, etc.)
def calculate_performance(cm):
    true_positives_rate = np.trace(cm) / np.sum(cm) * 100  # Calculate accuracy from confusion matrix
    print(cm)
    print(np.trace(cm), np.sum(cm),'miau')
    if cm.shape == (1,1):
        cm = np.array([[0,0],[0,cm[0][0]]])
    print(true_positives_rate)
    true_positives = cm[1, 1]
    #true_negative_rate = cm[0, 0] / (cm[0, 0] + cm[0, 1]) * 100  # TNR from confusion matrix
    return true_positives_rate, true_positives#, true_negative_rate

# Function to test a model on LASER data of different types (Title, Abstract, Both)
def test_model_on_laser_data(model, X_title, X_abstract, X_both, y_true):
    # Predict on Title, Abstract, Both (LASER dataset inputs)
    preds_title = model.predict(X_title)
    preds_abstract = model.predict(X_abstract)
    preds_both = model.predict(X_both)
    
    neg_index = [ np.where(preds_title == 0)[0],
                 np.where(preds_abstract == 0)[0],
                 np.where(preds_both == 0)[0]
    ]
    print(np.where(preds_title == 0)[0])
    ranges = np.concatenate(neg_index)
    ranges = set(ranges.flatten())
    # Calculate confusion matrices for each
    cm_title = confusion_matrix(y_true, preds_title)
    cm_abstract = confusion_matrix(y_true, preds_abstract)
    cm_both = confusion_matrix(y_true, preds_both)
    print(cm_title.ravel())
    print(cm_abstract.ravel())
    print(cm_both.ravel())

    print(cm_title)
    print(cm_abstract)
    print(cm_both,'both')
    # Calculate performance metrics for each input type
    title_metrics = calculate_performance(cm_title)
    abstract_metrics = calculate_performance(cm_abstract)
    both_metrics = calculate_performance(cm_both)
    
    return title_metrics, abstract_metrics, both_metrics, list(ranges)


   
    

def transform_LASER_data(vectorizer, transformer, raw_title, raw_abstract, raw_both):
    pipeline = make_pipeline(vectorizer, transformer)
    X_title = pipeline.transform(raw_title)
    X_abstract = pipeline.transform(raw_abstract)
    X_both = pipeline.transform(raw_both)
    return X_title, X_abstract, X_both, pipeline

def print_and_explain(abstract_metrics, pipeline, model, raw_title, raw_abstract):
    rel_index = abstract_metrics[-1][:2]
    sample_data_title = raw_title.iloc[rel_index]
    sample_data_abstract = raw_abstract.iloc[rel_index]
    
    for sample_title, sample_abstract in zip(sample_data_title,sample_data_abstract):
        explain_with_lime(pipeline, model, sample_data=sample_title)    
        explain_with_lime(pipeline, model, sample_data=sample_abstract)    
        explain_with_lime(pipeline, model, sample_data=sample_title+sample_abstract)    



def create_performance_matrices(title_metrics, abstract_metrics, both_metrics):
    metrics_matrix = np.array([
        [title_metrics[0][0], title_metrics[1][0], title_metrics[2][0]],   # Model trained on Title
        [abstract_metrics[0][0], abstract_metrics[1][0], abstract_metrics[2][0]],   # Model trained on Abstract
        [both_metrics[0][0], both_metrics[1][0], both_metrics[2][0]]   # Model trained on Both
    ])
    total_matrix = np.array([
        [title_metrics[0][1], title_metrics[1][1], title_metrics[2][1]],   # Model trained on Title
        [abstract_metrics[0][1], abstract_metrics[1][1], abstract_metrics[2][1]],   # Model trained on Abstract
        [both_metrics[0][1], both_metrics[1][1], both_metrics[2][1]]   # Model trained on Both
    ])
    return metrics_matrix, total_matrix

def display_performance_metrics(model_name, metrics_matrix, total_matrix):
    metrics_df = pd.DataFrame(metrics_matrix, index=['Trained on Title', 'Trained on Abstract', 'Trained on Both'],
                              columns=['Tested on Title', 'Tested on Abstract', 'Tested on Both'])
    total_df = pd.DataFrame(total_matrix, index=['Trained on Title', 'Trained on Abstract', 'Trained on Both'],
                            columns=['Tested on Title', 'Tested on Abstract', 'Tested on Both'])
    
    print(f"\nPerformance Comparison for {model_name}:\n")
    print(metrics_df)
    combined_matrix = create_combined_matrix(metrics_matrix, total_df)
    plot_matriz_conf(metrics_matrix, combined_matrix)

def compare_models_on_laser(model_name, model_info, raw_title, raw_abstract, raw_both, y_true):
    # Model trained on Title
    vectorizer = model_info['Title']['vectorizer']
    transformer = model_info['Title']['transformer']
    X_title, X_abstract, X_both, pipeline_title = transform_LASER_data(vectorizer, transformer, raw_title, raw_abstract, raw_both)
    title_metrics = test_model_on_laser_data(model_info['Title']['model'], X_title, X_abstract, X_both, y_true)

    print('Trained_on_title')
    print_and_explain(title_metrics, pipeline_title, model_info['Title']['model'], raw_title, raw_abstract)
    

    # Model trained on Abstract
    vectorizer = model_info['Abstract']['vectorizer']
    transformer = model_info['Abstract']['transformer']
    X_title, X_abstract, X_both, pipeline_abstract = transform_LASER_data(vectorizer, transformer, raw_title, raw_abstract, raw_both)
    abstract_metrics = test_model_on_laser_data(model_info['Abstract']['model'], X_title, X_abstract, X_both, y_true)
    
    print('Trained_on_Abstract')

    print_and_explain(abstract_metrics, pipeline_abstract, model_info['Abstract']['model'], raw_title, raw_abstract)

    # Model trained on Both
    vectorizer = model_info['Both']['vectorizer']
    transformer = model_info['Both']['transformer']
    X_title, X_abstract, X_both, pipeline_both = transform_LASER_data(vectorizer, transformer, raw_title, raw_abstract, raw_both)
    both_metrics = test_model_on_laser_data(model_info['Both']['model'], X_title, X_abstract, X_both, y_true)
    print('Trained_on_Both')

    print_and_explain(both_metrics, pipeline_both, model_info['Both']['model'], raw_title, raw_abstract)

    # Create and display performance matrices
    metrics_matrix, total_matrix = create_performance_matrices(title_metrics, abstract_metrics, both_metrics)
    display_performance_metrics(model_name, metrics_matrix, total_matrix)

    return metrics_matrix
    
def create_combined_matrix(metrics_matrix, total_df):
    combined_matrix = np.empty(metrics_matrix.shape, dtype=object)
    for i in range(metrics_matrix.shape[0]):
        for j in range(metrics_matrix.shape[1]):
            number_papers = int(total_df.iloc[i, j])
            percentage = metrics_matrix[i, j]
            combined_matrix[i, j] = f"{number_papers}\n({percentage:.1f}%)"
    return combined_matrix


# Update the plot function
def plot_matriz_conf(cm, annot_matrix=True,fmt="", ac=None, **kwargs):
    ''' Plot a heatmap with annotations.'''
    
    plt.figure(figsize=(8,6))

    print(cm,annot_matrix)
    ax = sns.heatmap(cm, annot=annot_matrix, fmt=fmt, linewidths=.5, square=True,
                     cmap=sns.color_palette('Blues', 9), annot_kws={'size': 20})
    if len(cm) == 3:
        ax.set_xticklabels(['Title','Abstract','Both'], fontsize=14,
                           fontweight='bold')
        ax.set_yticklabels(['Title','Abstract','Both'], fontsize=14,
                           fontweight='bold')
        plt.ylabel('Trained on', fontsize=16, fontweight='bold')
        plt.xlabel('Tested on', fontsize=16, fontweight='bold')
        all_sample_title = 'Number of LASER articles retrieved'
    else:
        ax.set_xticklabels(['False','True'], fontsize=14, fontweight='bold')
        ax.set_yticklabels(['False','True'], fontsize=14, fontweight='bold')
        plt.ylabel('Actual label', fontsize=16, fontweight='bold')
        plt.xlabel('Predicted label', fontsize=16, fontweight='bold')
        all_sample_title = 'Accuracy Score: {0}'.format(ac)
    plt.title(all_sample_title, size=15)
    plt.show()

