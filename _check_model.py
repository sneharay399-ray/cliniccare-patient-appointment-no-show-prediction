import os, json, sys

model_path = 'healthcare-app/ml-service/model.joblib'
metrics_path = 'healthcare-app/ml-service/model_metrics.json'

if os.path.exists(model_path):
    size = os.path.getsize(model_path)
    print('model.joblib: {} bytes'.format(size))
else:
    print('model.joblib: NOT FOUND (will be trained on first run)')

if os.path.exists(metrics_path):
    with open(metrics_path) as f:
        m = json.load(f)
    print('model_metrics.json: ROC-AUC={}, Accuracy={}, F1={}'.format(
        m.get('roc_auc'), m.get('accuracy'), m.get('f1_score')))
else:
    print('model_metrics.json: NOT FOUND (will be generated on first run)')
