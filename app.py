#!/usr/bin/env python

import os
from os.path import abspath, dirname, join
from flask import flash, Flask, render_template, request
import mistune

from scorer import SOTGScorer, InvalidURLException

HERE = dirname(abspath(__file__))
README = join(HERE, 'README.md')
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'Super secret key')


def get_usage():
    """Return rendered HTML of the Usage section from README.md."""
    usage = ''
    for line in open(README):
        if not usage and not line.startswith('## Usage'):
            continue
        elif usage and line.startswith('## ') and not line.startswith('## Usage'):
            break
        else:
            usage += line
    return mistune.markdown(usage, escape=False)


@app.route('/', methods=['GET'])
def index():
    url = request.args.get('url')
    columns = {
        'team': request.args.get('team'),
        'opponent': request.args.get('opponent'),
        'day': request.args.get('day'),
        'team-score-columns': request.args.getlist('team-score-columns'),
        'opponent-score-columns': request.args.getlist('opponent-score-columns'),
    }

    rankings = None
    received_scores = awarded_scores = all_columns = []
    errors = []
    prompt_column_select = False

    if not url:
        pass

    elif not all(columns.values()):
        try:
            scorer = SOTGScorer(url)
        except InvalidURLException as e:
            errors.append('Invalid URL - {}'.format(e))
        else:
            all_columns = list(scorer.data.columns)
            try:
                rankings, received_scores, awarded_scores = scorer.all_scores
            except Exception as e:
                prompt_column_select = True
                errors.append('Failed to compute rankings: {}'.format(e))

    else:
        scorer = SOTGScorer(url, columns=columns)
        rankings, received_scores, awarded_scores = scorer.all_scores
        all_columns = list(scorer.data.columns)

    for e in errors:
        flash(e, 'error')

    return render_template('index.html.jinja',
                           errors=errors,
                           usage=get_usage(),
                           columns=columns,
                           all_columns=all_columns,
                           url=url,
                           prompt_column_select=prompt_column_select,
                           rankings=rankings,
                           received_scores=received_scores,
                           awarded_scores=awarded_scores)


if __name__ == '__main__':
    app.run(debug=True)
