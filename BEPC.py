import base64
import io
import dash
from dash import html, dcc, dash_table, Input, Output, State
import pandas as pd
import tabula
from collections import Counter

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    dcc.Upload(
        id='upload-pdf',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select PDF File')
        ]),
        style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    html.Div([
        dcc.Dropdown(id='column-dropdown', placeholder="Select a column"),
        dcc.Dropdown(id='word-dropdown', placeholder="Select a word")
    ]),
    html.Div(id='word-count-output'),
    html.Div(id='output-data-table')
])

def parse_pdf(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = tabula.read_pdf(io.BytesIO(decoded), lattice=True, pages="all")
        df = pd.concat(df, ignore_index=True, join="inner",  )
        # Remove the first row
   
      #  df = df[0].drop(["Unnamed: 0"],axis=0)
      # Remove any unnamed columns
        #df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        # Remove the header by resetting column names
        df.columns = ['IRE', 'RANG', 'EX','PRENOM et NOM', 'CENTRE', 'PV', 'ORIGINE', 'Mention']
        df = df.iloc[1:].reset_index(drop=True)
        return df
    except Exception as e:
        print(e)
        return pd.DataFrame()

@app.callback(
    Output('column-dropdown', 'options'),
    Output('output-data-table', 'children'),
    Input('upload-pdf', 'contents'),
    State('upload-pdf', 'filename')
)
def update_output(contents, filename):
    if contents is not None:
        df = parse_pdf(contents, filename)
        
        column_options = [{'label': col, 'value': col} for col in df.columns]
        
        table = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=10,
            style_table={'height': '300px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': 'lightgrey',
                'fontWeight': 'bold'
            }
        )
        
        return column_options, table
    
    return [], html.Div()

@app.callback(
    Output('word-dropdown', 'options'),
    Input('column-dropdown', 'value'),
    State('upload-pdf', 'contents'),
    State('upload-pdf', 'filename')
)
def update_word_dropdown(selected_column, contents, filename):
    if contents is not None and selected_column is not None:
        df = parse_pdf(contents, filename)
        words = df[selected_column].astype(str).str.split(expand=True).stack().unique()
        return [{'label': word, 'value': word} for word in words]
    return []

@app.callback(
    Output('word-count-output', 'children'),
    Input('column-dropdown', 'value'),
    Input('word-dropdown', 'value'),
    State('upload-pdf', 'contents'),
    State('upload-pdf', 'filename')
)
def update_word_count(selected_column, selected_word, contents, filename):
    if contents is not None and selected_column is not None and selected_word is not None:
        df = parse_pdf(contents, filename)
        word_counts = Counter(' '.join(df[selected_column].astype(str)).split())
        count = word_counts[selected_word]
        return f"L'école {selected_word} a eu {count} admis !"
    return ""

if __name__ == '__main__':
    app.run_server(debug=True)